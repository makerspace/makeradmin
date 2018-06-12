$(document).ready(() => {
  // Create a Stripe client.
  const stripe = Stripe(window.stripeKey);
  const apiBasePath = window.apiBasePath;

  // Create an instance of Elements.
  const elements = stripe.elements({ locale: "sv" });

  // Custom styling can be passed to options when creating an Element.
  // (Note that this demo uses a wider set of styles than the guide below.)
  const style = {
    base: {
      color: '#32325d',
      lineHeight: '18px',
      fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
      fontSmoothing: 'antialiased',
      fontSize: '16px',
      '::placeholder': {
        color: '#8a8f94'
      }
    },
    invalid: {
      color: '#fa755a',
      iconColor: '#fa755a'
    }
  };

  // Create an instance of the card Element.
  const card = elements.create('card', {style: style});

  // Add an instance of the card Element into the `card-element` <div>.
  card.mount('#card-element');

  // Used to prevent clicking the 'Pay' button twice
  const duplicatePurchaseRand = (100000000*Math.random())|0;

  const currency = "kr";
  const currencyBase = 100;

  const id2item = new Map();

  const data = JSON.parse($("#product-data")[0].textContent);

  for (const cat of data) {
    for (const item of cat.items) {
      id2item.set(item.id, item);
    }
  }

  let cart = [];

  function sumCart(cart) {
    let totalSum = 0;
    for (let item of cart) {
      totalSum += item.count * id2item.get(item.id).price;
    }
    return totalSum;
  }

  function refresh() {
    let checked = $(".uk-radio:checked");
    // Should only have 1 checked radio button
    if (checked.length !== 1) throw "more than one checked radio button";

    cart = [{
      id: $(checked[0]).val()|0,
      count: 1,
    }];

    const totalSum = sumCart(cart);
    $("#pay-button").find("span").html("Betala " + ((totalSum*currencyBase)|0)/currencyBase + " " + currency);
  }

  $(".uk-radio").on("change input", ev => {
    refresh();
  });

  let waitingForPaymentResponse = false;
  $("#pay-button").click((ev) => {
    ev.preventDefault();

    // Don't allow any clicks while waiting for a response from the server
    if (waitingForPaymentResponse) {
      return;
    }

    waitingForPaymentResponse = true;

    $(".pay-spinner").toggleClass("pay-spinner-visible", true);
    let errorElement = document.getElementById('card-errors');
    errorElement.textContent = "";

    stripe.createSource(card).then(function(result) {
      if (result.error) {
        $(".pay-spinner").toggleClass("pay-spinner-visible", false);
        // Inform the user if there was an error.
        errorElement.textContent = result.error.message;
        waitingForPaymentResponse = false;
      } else {
        $.ajax({
          type: "POST",
          url: apiBasePath + "/webshop/register",
          data: JSON.stringify({
            member: {
              firstname: $("#firstname").val(),
              lastname: $("#lastname").val(),
              email: $("#email").val(),
              phone: $("#phone").val(),
              address_street: "", // $("#address_street").val(),
              address_extra: "", // $("#address_extra").val(),
              address_zipcode: "", // $("#address_zipcode").val(),
              address_city: "", // $("#address_city").val(),
            },
            purchase: {
              cart: cart,
              expectedSum: sumCart(cart),
              stripeSource: result.source.id,
              duplicatePurchaseRand: duplicatePurchaseRand,
            }
          }),
          contentType: "application/json; charset=utf-8",
          dataType: "json",
          headers: {
            "Authorization": "Bearer " + localStorage.token
          }
        }).done((data, textStatus, xhr) => {
          $(".progress-spinner").toggleClass("progress-spinner-visible", false);
          waitingForPaymentResponse = false;
          if (xhr.responseJSON.data.redirect !== undefined) {
            window.location.href = xhr.responseJSON.data.redirect;
          } else {
            window.location.href = "receipt/" + xhr.responseJSON.data.transaction_id;
          }
        }).fail((xhr, textStatus, error) => {
          $(".pay-spinner").toggleClass("pay-spinner-visible", false);
          waitingForPaymentResponse = false;
          if (xhr.responseJSON.status == "The value needs to be unique in the database") {
            UIkit.modal.alert("<h2>Registreringen misslyckades</h2>En användare med denna email är redan registrerad");
          } else {
            UIkit.modal.alert("<h2>Betalningen misslyckades</h2>" + xhr.responseJSON.status);
          }
        });
      }
    });
  });

  refresh();
});