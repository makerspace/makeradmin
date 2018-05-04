$(document).ready(() => {
  // Create a Stripe client.
  var stripe = Stripe('pk_test_bzZLzeh8RXxM8nnEloZdisTp');
  let apiBasePath = "http://" + window.location.hostname + ":8010";

  // Create an instance of Elements.
  var elements = stripe.elements({ locale: "sv" });

  // TODO: Figure out from access token
  // Preferably without an extra HTTP request
  const isAdmin = true;

  function showEdit() {
    $("#edit").toggleClass("active");
    $("#edit").click(() => {
      $(".edit, .edit-display, .edit-invisible").toggleClass("active");
      $(".edit, .edit-display").toggleClass("disabled");
    })
  }

  if (isAdmin) {
    showEdit();
  }

  // Custom styling can be passed to options when creating an Element.
  // (Note that this demo uses a wider set of styles than the guide below.)
  var style = {
    base: {
      color: '#32325d',
      lineHeight: '18px',
      fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
      fontSmoothing: 'antialiased',
      fontSize: '16px',
      '::placeholder': {
        color: '#aab7c4'
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

  const currency = "kr";
  const currencyBase = 100;

  var cart = [];
  var id2element = new Map();
  var id2cartItem = new Map();
  var id2item = new Map();

  var data = JSON.parse($("#product-data")[0].textContent);

  for (const cat of data) {
    const catLi = `
      <li><h3 id="category${cat.id}">${cat.name}</h3></li>
    `;

    $(".product-list").append($(catLi));
    for (const item of cat.items) {
      let base = 1;

      // Do integer math for stability
      // Calculate a reasonable pricing amount to show
      // (e.g 5kr/100g instead of 0.05kr/g)
      let price = (item.price*currencyBase)|0;
      if (price > 0 && (item.unit == "g" || item.unit == "mm" || item.unit == "ml")) {
        for (multiplier of [1, 100, 1000]) {
          base = multiplier;

          // Check if value is representable with at most one decimal
          if(((price*base) % (currencyBase/10)) == 0) break;
        }
        price *= multiplier;
      }
      price /= currencyBase;

      let baseStr = base > 1 ? base + item.unit : item.unit;

      const buttons = [];
      const increments = [1, 10, 100];
      for (const incr of increments) {
        buttons.push(`<button class="uk-button uk-button-small uk-button-primary number-add" data-amount="${incr}">+${incr}${item.unit}</button>`);
      }

      const li = $(
        `<li>
            <form class="product">
                <span class="product-title">${item.name}</span>
                <span class="product-price">${price} ${currency}/${baseStr}</span>
                <input type="number" placeholder="0" class="product-amount edit-invisible"></input>
                <span class="product-unit edit-invisible">${item.unit}</span>
                <div class="product-actions">
                  <span class="edit-display disabled">
                    <a href="product/${item.id}/edit" class="edit-display disabled product-edit uk-button uk-button-small uk-button-primary" uk-icon="pencil" />
                    <button class="edit-display disabled product-delete uk-button uk-button-small uk-button-danger" uk-icon="trash" />
                  </span>
                  <span class="edit-invisible">
                    ${ buttons.join("\n") }
                  </span>
                </div>
            </form>
        </li>`);
      id2element.set(item.id, li);
      id2item.set(item.id, item);

      // Handle deleting products
      li.find(".product-delete").click((ev) => {
        ev.preventDefault();
        UIkit.modal.confirm(`Are you sure you want to delete ${item.name}?`).then(
          () => {
            $.ajax({
              type: "DELETE",
              url: apiBasePath + "/webshop/product/" + item.id,
              data: JSON.stringify({
                id: item.id,
              }),
              contentType: "application/json; charset=utf-8",
              dataType: "json",
              headers: {
                "Authorization": "Bearer " + localStorage.token
              }
            }).done(() => {
              li.remove();
            }).fail((xhr, textStatus, error) => {
              UIkit.modal.alert("<h2>Error</h2>" + xhr.responseJSON.status);
            });
        });
      });

      $(li).find(".product-amount").on("input change", ev => {
        refresh();
        ev.preventDefault();
      });

      $(li).find(".number-add").click(ev => {
        const amount = li.find(".product-amount");
        amount.val((amount.val()|0)+($(ev.currentTarget).attr("data-amount")|0));
        amount.change();
        ev.preventDefault();
      });

      $(".product-list").append(li);
    }
  }

  function sumCart(cart) {
    let totalSum = 0;
    for (let item of cart) {
      totalSum += item.count * id2item.get(item.id).price;
    }
    return totalSum;
  }

  function refresh() {
    cart = [];
    
    // $(".product-list").find(".product-amount").each(function() {
    for (var [id, elem] of id2element.entries()) {
      const amountElem1 = $(elem).find(".product-amount");
      const amountElem2 = id2cartItem.has(id) ? id2cartItem.get(id).find(".product-amount") : null;
      let selected = amountElem1.is(":focus");
      if (amountElem2 !== null) selected |= amountElem2.is(":focus");

      var count = amountElem1.val()|0;
      if (count > 0 || selected) {
        cart.push({
          id: id,
          count: count,
        });
      }
      $(elem).find(".product-active-dot").toggleClass("active", count > 0);
    }

    let totalSum = sumCart(cart);

    $("#pay-button").val("Betala " + ((totalSum*currencyBase)|0)/currencyBase + " " + currency);

    $("#pay-module").toggleClass("open", cart.length > 0);

    var marked = new Set();
    for (var i = 0; i < cart.length; i++) {
      const cartItem = cart[i];
      const item = id2item.get(cartItem.id);
      if (!id2cartItem.has(item.id)) {
        const li = $(
          `<li>
            <form class="product">
            <span class="product-title">${item.name}</span>
            <span class="product-price">${item.price} ${currency}/${item.unit}</span>
            <input type="number" placeholder="0" class="product-amount"></input>
            <span class="product-unit">${item.unit}</span>
            <button class="uk-button uk-button-small uk-button-danger product-remove" uk-icon="trash"></button>
          </form>
          </li>`
        );
        li.find(".product-remove").click(ev => {
          const amount = $(id2element.get(item.id)).find(".product-amount");
          amount.val(0);
          amount.change();
          ev.preventDefault();
        });
        li.find(".product-amount").on("input change", ev => {
          const amountElem = $(id2element.get(item.id)).find(".product-amount");
          amountElem.val($(ev.currentTarget).val());
          amountElem.change();
        });
        id2cartItem.set(item.id, li);
        $("#cart").append(li);
      }

      $(id2cartItem.get(item.id)).find(".product-amount").val(cartItem.count);

      marked.add(item.id);
    }

    console.log(marked);
    console.log(id2cartItem);
    var toDelete = [];
    for (var key of id2cartItem.keys()) {
      if (!marked.has(key)) toDelete.push(key);
    }

    console.log(toDelete);
    for (var i = 0; i < toDelete.length; i++) {
      $(id2cartItem.get(toDelete[i])).remove();
      id2cartItem.delete(toDelete[i]);
    }
  }

  $("#pay").submit((ev) => {
    ev.preventDefault();
    stripe.createToken(card).then(function(result) {
      if (result.error) {
        // Inform the user if there was an error.
        var errorElement = document.getElementById('card-errors');
        errorElement.textContent = result.error.message;
      } else {
        $.ajax({
          type: "POST",
          url: apiBasePath + "/webshop/pay",
          data: JSON.stringify({
            cart: cart,
            expectedSum: sumCart(cart),
            stripeToken: result.token.id
          }),
          contentType: "application/json; charset=utf-8",
          dataType: "json",
          headers: {
            "Authorization": "Bearer " + localStorage.token
          }
        }).done((data, textStatus, xhr) => {
          UIkit.modal.alert("Betalningen har genomförts");
        }).fail((xhr, textStatus, error) => {
          if (xhr.responseJSON.message == "Unauthorized") {
            UIkit.modal.alert("<h2>Betalningen misslyckades</h2>Du är inte inloggad");
          } else {
            UIkit.modal.alert("<h2>Betalningen misslyckades</h2>" + xhr.responseJSON.status);
          }
        });
        // Send the token to your server.
        //stripeTokenHandler(result.token);
        console.log(result.token);
      }
    });
  });

  $(".category-delete").click(ev => {
    ev.preventDefault();
    const id = $(ev.currentTarget).attr("data-id");

    UIkit.modal.confirm(`Are you sure you want to delete this category?`).then(
      () => {
        $.ajax({
          type: "DELETE",
          url: apiBasePath + "/webshop/category/" + id,
          data: JSON.stringify({ id: id }),
          contentType: "application/json; charset=utf-8",
          dataType: "json",
          headers: {
            "Authorization": "Bearer " + localStorage.token
          }
        }).done(() => {
          location.reload(true);
        }).fail((xhr, textStatus, error) => {
          UIkit.modal.alert("<h2>Error</h2>" + xhr.responseJSON.status);
        });
    });
  });

  $(".category-add").click(ev => {
    ev.preventDefault();
    UIkit.modal.prompt('Category Name', '').then(name => {
      if (name == null) return;

      $.ajax({
        type: "POST",
        url: apiBasePath + "/webshop/category",
        data: JSON.stringify({ name: name }),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        headers: {
          "Authorization": "Bearer " + localStorage.token
        }
      }).done((data, textStatus, xhr) => {
        // Reload the page to show the new category
        location.reload(true);
      }).fail((xhr, textStatus, error) => {
        if (xhr.responseJSON.message == "Unauthorized") {
          UIkit.modal.alert("<h2>Något gick fel</h2>Du har inte behörighet att lägga till en ny kategori");
        } else {
          UIkit.modal.alert("<h2>Något gick fel</h2>" + xhr.responseJSON.status);
        }
      });
    });
  })

  refresh();
});