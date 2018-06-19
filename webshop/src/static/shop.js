$(document).ready(() => {
  // Create a Stripe client.
  const stripe = Stripe(window.stripeKey);
  const apiBasePath = window.apiBasePath;
  const webshop_edit_permission = "webshop_edit";

  // Create an instance of Elements.
  const elements = stripe.elements({ locale: "sv" });

  // Used to prevent clicking the 'Pay' button twice
  const duplicatePurchaseRand = (100000000*Math.random())|0;

  let editMode = false;

  function setEditMode(value) {
    editMode = value;
    $(".edit, .edit-display, .edit-invisible").toggleClass("active", editMode);
    $("#edit").toggleClass("edit-mode", editMode);
    $("#edit").attr("uk-icon", editMode ? "close" : "pencil");
    refresh();
  }

  function showEditButton() {
    $("#edit").toggleClass("active");
    $("#edit").click(() => {
      setEditMode(!editMode);
    })
  }

  function setLoggedIn (loggedIn) {
    $("#pay-login").toggleClass("active", !loggedIn);
    $("#pay").toggleClass("active", loggedIn);
  }

  function ajax(type, url, data) {
      return $.ajax({
          type: type,
          url: url,
          data: JSON.stringify(data),
          contentType: "application/json; charset=utf-8",
          dataType: "json",
          headers: {
              "Authorization": "Bearer " + localStorage.token
          }
      });
  }

  function refreshLoggedIn () {
    $.ajax({
      type: "GET",
      url: apiBasePath + "/member/current/permissions",
      headers: {
        "Authorization": "Bearer " + localStorage.token
      }
    }).done((data, textStatus, xhr) => {
      setLoggedIn(true);
      const permissions = xhr.responseJSON.data.permissions;
      if (permissions.indexOf(webshop_edit_permission) !== -1) showEditButton();
    }).fail((xhr, textStatus, error) => {
      if (xhr.status == 401) {
        setLoggedIn(false);
      } else {
        UIkit.modal.alert("<h2>Error</h2>" + xhr.responseJSON.status + "\n" + xhr.responseJSON.message);
      }
    });
  }

  function login() {
    ajax("POST", apiBasePath + "/member/send_access_token", {
      user_tag: $("#email").val(),
      redirect: "shop"
    }).done(() => {
      UIkit.modal.alert("En inloggningslänk har skickats via email");
    }).fail((xhr, textStatus, error) => {
      if (xhr.responseJSON.status == "not found") {
        UIkit.modal.alert("Ingen medlem med denna email hittades");
      } else {
        UIkit.modal.alert("<h2>Error</h2>" + xhr.responseJSON.status + " " + xhr.responseJSON.message);
      }
    });
  }

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

  const id2element = new Map();
  const id2cartItem = new Map();
  const id2item = new Map();
  const data = JSON.parse($("#product-data")[0].textContent);

  for (const cat of data) {
    const catLi = `
      <li><h3 id="category${cat.id}">${cat.name}</h3></li>
    `;

    $(".product-list").append($(catLi));
    for (const item of cat.items) {
      let price = item.price;
      price *= item.smallest_multiple;

      let baseStr = item.smallest_multiple > 1 ? item.smallest_multiple + item.unit : item.unit;

      const buttons = [];
      let increments = [1, 10, 100];
      if (item.smallest_multiple != 1) {
        increments = [item.smallest_multiple, 2*item.smallest_multiple, 3*item.smallest_multiple];
      }

      for (const incr of increments) {
        buttons.push(`<button type="button" class="uk-button uk-button-small uk-button-primary number-add" data-amount="${incr}">+${incr}${item.unit}</button>`);
      }

      const li = $(
        `<li>
            <div class="product">
                <span class="product-title">${item.name}</span>
                <span class="product-price">${price} ${currency}/${baseStr}</span>
                <input type="number" min=0 step=${item.smallest_multiple} placeholder="0" class="product-amount edit-invisible"></input>
                <span class="product-unit edit-invisible">${item.unit}</span>
                <div class="product-actions">
                  <span class="edit-display">
                    <a href="product/${item.id}/edit" class="edit-display product-edit uk-button uk-button-small uk-button-primary" uk-icon="pencil" />
                    <button type="button" class="edit-display product-delete uk-button uk-button-small uk-button-danger" uk-icon="trash" />
                  </span>
                  <span class="edit-invisible">
                    ${ buttons.join("\n") }
                  </span>
                </div>
            </div>
        </li>`);
      id2element.set(item.id, li);
      id2item.set(item.id, item);

      // Handle deleting products
      li.find(".product-delete").click((ev) => {
        ev.preventDefault();
        UIkit.modal.confirm(`Are you sure you want to delete ${item.name}?`).then(
          () => {
            ajax("DELETE", apiBasePath + "/webshop/product/" + item.id, {
            }).done(() => {
              li.remove();
            }).fail((xhr, textStatus, error) => {
              UIkit.modal.alert("<h2>Error</h2>" + xhr.responseJSON.status);
            });
        });
      });

      $(li).find(".product-amount").on("input", ev => {
        refresh();
      });

      $(li).find(".product-amount").on("change", ev => {
        if ($(ev.currentTarget).val() != "") {
          let newAmount = (Math.ceil($(ev.currentTarget).val() / item.smallest_multiple)*item.smallest_multiple)|0;
          $(ev.currentTarget).val(newAmount);
        }
        refresh();
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

  function parseCartFromStorage() {
    let cart = [];
    try {
      cart = JSON.parse(localStorage.getItem("cart"));
    } catch (e) {}

    if (!Array.isArray(cart)) {
      cart = [];
    }

    for (const item of cart) {
      const element = id2element.get(item.id);
      if (element !== null && element !== undefined) {
        element.find(".product-amount").val(item.count);
        element.find(".product-amount").change();
      }
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

      let raw_count = amountElem1.val()|0;
      let count = (Math.ceil(raw_count / id2item.get(id).smallest_multiple)*id2item.get(id).smallest_multiple)|0;
      if (count > 0 || selected) {
        cart.push({
          id: id,
          count: count,
          raw_count: raw_count,
        });
      }
    }

    localStorage.cart = JSON.stringify(cart);

    let totalSum = sumCart(cart);

    $("#pay-button").find("span").html("Betala " + ((totalSum*currencyBase)|0)/currencyBase + " " + currency);

    $("#pay-module").toggleClass("open", cart.length > 0 && !editMode);

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
            <input type="number" min=0 step=${item.smallest_multiple} placeholder="0" class="product-amount"></input>
            <span class="product-unit">${item.unit}</span>
            <button type="button" class="uk-button uk-button-small uk-button-danger product-remove" uk-icon="trash"></button>
          </form>
          </li>`
        );
        li.find(".product-remove").click(ev => {
          const amount = $(id2element.get(item.id)).find(".product-amount");
          amount.val("");
          amount.change();
          ev.preventDefault();
        });
        li.find(".product-amount").on("input", ev => {
          const amountElem = $(id2element.get(item.id)).find(".product-amount");
          amountElem.val($(ev.currentTarget).val());
          refresh();
        });
        li.find(".product-amount").on("change", ev => {
          const amountElem = $(id2element.get(item.id)).find(".product-amount");
          const newAmount = (Math.ceil($(ev.currentTarget).val() / item.smallest_multiple)*item.smallest_multiple)|0;
          amountElem.val(newAmount);
          refresh();
        });
        id2cartItem.set(item.id, li);
        $("#cart").append(li);
      }

      $(id2cartItem.get(item.id)).find(".product-amount").val(cartItem.raw_count);

      marked.add(item.id);
    }

    var toDelete = [];
    for (var key of id2cartItem.keys()) {
      if (!marked.has(key)) toDelete.push(key);
    }

    for (var i = 0; i < toDelete.length; i++) {
      $(id2cartItem.get(toDelete[i])).remove();
      id2cartItem.delete(toDelete[i]);
    }
  }

  let waitingForPaymentResponse = false;

  function pay() {
    // Don't allow any clicks while waiting for a response from the server
    if (waitingForPaymentResponse) {
      return;
    }

    waitingForPaymentResponse = true;

    $(".progress-spinner").toggleClass("progress-spinner-visible", true);
    let errorElement = document.getElementById('card-errors');
    errorElement.textContent = "";

    stripe.createSource(card).then(function(result) {
      if (result.error) {
        $(".progress-spinner").toggleClass("progress-spinner-visible", false);
        // Inform the user if there was an error.
        errorElement.textContent = result.error.message;
        waitingForPaymentResponse = false;
      } else {
        ajax("POST", apiBasePath + "/webshop/pay", {
          cart: cart,
          expectedSum: sumCart(cart),
          stripeSource: result.source.id,
          duplicatePurchaseRand: duplicatePurchaseRand,
        }).done((data, textStatus, xhr) => {
          $(".progress-spinner").toggleClass("progress-spinner-visible", false);
          waitingForPaymentResponse = false;
          localStorage.setItem("cart", "");
          if (xhr.responseJSON.data.redirect !== undefined) {
            window.location.href = xhr.responseJSON.data.redirect;
          } else {
            window.location.href = "receipt/" + xhr.responseJSON.data.transaction_id;
          }
          // UIkit.modal.alert("Betalningen har genomförts");
        }).fail((xhr, textStatus, error) => {
          $(".progress-spinner").toggleClass("progress-spinner-visible", false);
          waitingForPaymentResponse = false;
          if (xhr.responseJSON.message == "Unauthorized") {
            UIkit.modal.alert("<h2>Betalningen misslyckades</h2>Du är inte inloggad");
          } else {
            UIkit.modal.alert("<h2>Betalningen misslyckades</h2>" + xhr.responseJSON.status);
          }
        });
      }
    });
  }

  function tryDeleteCategory(id) {
    UIkit.modal.confirm(`Are you sure you want to delete this category?`).then(
      () => {
        ajax("DELETE", apiBasePath + "/webshop/category/" + id, {
        }).done(() => {
          location.reload(true);
        }).fail((xhr, textStatus, error) => {
          UIkit.modal.alert("<h2>Error</h2>" + xhr.responseJSON.status);
        });
    });
  }

  function addCategory() {
    UIkit.modal.prompt('Category Name', '').then(name => {
      if (name == null) return;

      ajax("POST", apiBasePath + "/webshop/category", {
        name: name
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
  }

  $("#pay-login form").submit(ev => {
    ev.preventDefault();
    login();
  });

  setLoggedIn(localStorage.token !== undefined && localStorage.token !== null);
  refreshLoggedIn();

  let cart = [];
  parseCartFromStorage();

  $("#pay").submit((ev) => {
    ev.preventDefault();
    pay();
  });

  $(".category-delete").click(ev => {
    ev.preventDefault();
    const id = $(ev.currentTarget).attr("data-id");
    tryDeleteCategory(id);
  });

  $(".category-add").click(ev => {
    ev.preventDefault();
    addCategory();
  })

  refresh();

  if (window.location.hash == "#edit") {
    showEditButton();
    setEditMode(true);
  }
});