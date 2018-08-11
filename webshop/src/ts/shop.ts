import Cart from "./cart"
import * as common from "./common"
declare var UIkit: any;

document.addEventListener('DOMContentLoaded', () => {
  const apiBasePath = window.apiBasePath;
  const webshop_edit_permission = "webshop_edit";
  const service_permission = "service";

  let editMode = false;

  // Keep local storage in sync even though other tabs change it
  Cart.startLocalStorageSync(refreshUIFromCart);

  function updateCartSum(cart: Cart) {
    if (cart.items.length > 0) {
      document.querySelector("#cart-sum").textContent = " (" + Cart.formatCurrency(cart.sum(id2item)) + ")";
    } else {
      document.querySelector("#cart-sum").textContent = "";
    }
  }

  function setCartItem(productID: number, count: number) {
    let cart = Cart.fromStorage();
    cart.setItem(productID, count);
    cart.saveToStorage();
    updateCartSum(cart);
  }

  function setEditMode(value: boolean) {
    editMode = value;
    let els = document.querySelectorAll(".edit, .edit-display, .edit-invisible");
    for (let i = 0; i < els.length; i++) {
      els[i].classList.toggle("active", editMode);
    }
    document.querySelector("#edit").classList.toggle("edit-mode", editMode);
    document.querySelector("#edit").setAttribute("uk-icon", editMode ? "close" : "pencil");
  }

  function showEditButton() {
    document.querySelector("#edit").classList.toggle("active", true);
  }

  document.querySelector("#edit").addEventListener("click", ev => {
    setEditMode(!editMode);
  });

  function setLoggedIn (loggedIn: boolean) {
  }

  const id2element = new Map<number, HTMLElement>();
  const id2cartItem = new Map();
  const id2item = new Map();
  const data = JSON.parse(document.querySelector("#product-data").textContent);

  for (const cat of data) {
    const catLi = `
      <li><h3 id="category${cat.id}">${cat.name}</h3></li>
    `;

    document.querySelector(".product-list").insertAdjacentHTML("beforeend", catLi);
    for (const item of cat.items) {
      let price = item.price;
      price *= item.smallest_multiple;

      let baseStr = item.smallest_multiple > 1 ? item.smallest_multiple + item.unit : item.unit;

      const li = document.createElement("li");
      li.innerHTML = 
        `<div class="product">
              <a class="product-title" href="product/${item.id}">${item.name}</a>
              <span class="product-price">${price} ${Cart.currency}/${baseStr}</span>
              <input type="number" min=0 max=9999 step=${item.smallest_multiple} placeholder="0" class="product-amount edit-invisible"></input>
              <span class="product-unit edit-invisible">${item.unit}</span>
              <a href="product/${item.id}/edit" class="edit-display product-edit uk-button uk-button-small uk-button-primary" uk-icon="pencil"></a>
              <button type="button" class="edit-display product-delete uk-button uk-button-small uk-button-danger" uk-icon="trash" ></button>
              <button type="button" class="edit-invisible uk-button uk-button-small uk-button-primary number-add" data-amount="1">+</button>
          </div>`;
      id2element.set(item.id, li);
      id2item.set(item.id, item);

      // Handle deleting products
      li.querySelector(".product-delete").addEventListener("click", ev => {
        ev.preventDefault();
        UIkit.modal.confirm(`Are you sure you want to delete ${item.name}?`).then(
          () => {
            common.ajax("DELETE", apiBasePath + "/webshop/product/" + item.id, {
            }).then(json => {
              li.remove();
            }).catch(json => {
              UIkit.modal.alert("<h2>Error</h2>" + json.status);
            });
        });
      });

      const productAmount = <HTMLInputElement>li.querySelector(".product-amount");
      // Select everything in the textfield when clicking on it
      productAmount.onclick = () => {
        productAmount.select();
      };

      productAmount.oninput = ev => {
        let newAmount = Cart.adjustItemCount(Number(productAmount.value), item);
        setCartItem(item.id, newAmount);
      };

      productAmount.onchange = ev => {
        let newAmount = Cart.adjustItemCount(Number(productAmount.value), item);
        setCartItem(item.id, newAmount);
        if (newAmount != 0) {
          productAmount.value = "" + newAmount;
        } else {
          productAmount.value = "";
        }
      };

      li.querySelector(".number-add").addEventListener("click", ev => {
        productAmount.value = "" + (Number(productAmount.value)+Number((<HTMLElement>ev.currentTarget).getAttribute("data-amount")));
        productAmount.onchange(null);
        ev.preventDefault();
      });

      document.querySelector(".product-list").appendChild(li);
    }
  }

  function refreshUIFromCart(cart: Cart) {
    // Reset all values
    for (const element of id2element.values()) {
      (<HTMLInputElement>element.querySelector(".product-amount")).value = "";
    }

    // Copy from cart
    for (const item of cart.items) {
      const element = id2element.get(item.id);
      if (element !== null && element !== undefined) {
        (<HTMLInputElement>element.querySelector(".product-amount")).value = "" + item.count;
      }
    }

    updateCartSum(cart);
  }

  function tryDeleteCategory(id: number) {
    UIkit.modal.confirm(`Are you sure you want to delete this category?`).then(
      () => {
        common.ajax("DELETE", apiBasePath + "/webshop/category/" + id, {
        }).then(json => {
          location.reload(true);
        }).catch(json => {
          UIkit.modal.alert("<h2>Error</h2>" + common.get_error(json));
        });
    });
  }

  function editCategory(id: number, placeholder_name: string) {
    UIkit.modal.prompt('Category Name', placeholder_name).then((name: string) => {
      if (name == null) return;

      common.ajax("PUT", apiBasePath + "/webshop/category/" + id, {
        name: name
      }).then(json => {
        // Reload the page to show the new category
        location.reload(true);
      }).catch(json => {
        if (json.message == "Unauthorized") {
          UIkit.modal.alert("<h2>Något gick fel</h2>Du har inte behörighet att ändra kategorier");
        } else {
          UIkit.modal.alert("<h2>Något gick fel</h2>" + common.get_error(json));
        }
      });
    });
  }

  function addCategory() {
    UIkit.modal.prompt('Category Name', '').then((name: string) => {
      if (name == null) return;

      common.ajax("POST", apiBasePath + "/webshop/category", {
        name: name
      }).then(json => {
        // Reload the page to show the new category
        location.reload(true);
      }).catch(json => {
        if (json.message == "Unauthorized") {
          UIkit.modal.alert("<h2>Något gick fel</h2>Du har inte behörighet att lägga till en ny kategori");
        } else {
          UIkit.modal.alert("<h2>Något gick fel</h2>" + common.get_error(json));
        }
      });
    });
  }

  setLoggedIn(localStorage.getItem("token") !== undefined && localStorage.getItem("token") !== null);
  common.refreshLoggedIn((loggedIn, permissions) => {
    setLoggedIn(loggedIn);
    if (loggedIn && (permissions.indexOf(webshop_edit_permission) !== -1 || permissions.indexOf(service_permission) !== -1)) showEditButton();
  });
  refreshUIFromCart(Cart.fromStorage());

  document.querySelectorAll(".category-delete").forEach(el => {
      el.addEventListener("click", ev => {
          ev.preventDefault();
          const id = Number((<HTMLElement>ev.currentTarget).getAttribute("data-id"));
          tryDeleteCategory(id);
      });
  });

  document.querySelectorAll(".category-edit").forEach(el => {
      el.addEventListener("click", ev => {
          ev.preventDefault();
          const id = Number((<HTMLElement>ev.currentTarget).getAttribute("data-id"));
          editCategory(id, (<HTMLElement>ev.currentTarget).getAttribute("data-name"));
      });
  });

  document.querySelector(".category-add").addEventListener("click", ev => {
    ev.preventDefault();
    addCategory();
  });

  if (window.location.hash == "#edit") {
    showEditButton();
    setEditMode(true);
  }
});