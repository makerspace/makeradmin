import Cart from "./cart";
import * as shopsearch from "./shopsearch";
import * as common from "./common";
import { renderSidebarCategories } from "./category";
declare var UIkit: any;

common.onGetAndDocumentLoaded("/webshop/product_data", (productData: any) => {
  common.addSidebarListeners();

  const apiBasePath = window.apiBasePath;

  renderSidebarCategories(productData, true);

  // Keep local storage in sync even though other tabs change it
  Cart.startLocalStorageSync(refreshUIFromCart);

  const id2element = new Map<number, HTMLElement>();
  const id2item = new Map();

  function setCartItem(productID: number, count: number) {
    let cart = Cart.fromStorage();
    cart.setItem(productID, count);
    cart.saveToStorage();
    common.updateCartSum(cart, id2item);
  }

  const layoutModes: Set<string> = new Set<string>(["layout-grid", "layout-list", "layout-table"]);
  function setLayoutMode(mode: string | null) {
    if (mode == null || !layoutModes.has(mode)) {
      mode = "layout-grid";
    }
    localStorage.setItem("webshop-layout-mode", mode);

    layoutModes.forEach(element => {
      document.querySelector(".product-list")!.classList.toggle(element, element === mode);
      document.querySelector("#" + element)!.classList.toggle("selected", element === mode);
    });
  }

  document.querySelectorAll(".layout-button").forEach(function (elm) {
    elm.addEventListener("click", ev => {
      setLayoutMode(elm.id);
    });
  });

  // Load saved layout mode
  setLayoutMode(localStorage.getItem("webshop-layout-mode"));

  function setLoggedIn(loggedIn: boolean) {
  }

  const productListElem = document.querySelector(".product-list")!;
  for (const category of productData) {
    const catLi = `
      <li><h3 id="category${category.id}">${category.name}</h3></li>
    `;

    productListElem.insertAdjacentHTML("beforeend", catLi);
    const productListLi = document.createElement("li");
    productListLi.className = "product-container-list"
    for (const item of category.items) {
      let price = item.price;
      price *= item.smallest_multiple;

      let baseStr = item.smallest_multiple > 1 ? item.smallest_multiple + item.unit : item.unit;

      const li = document.createElement("div");
      li.className = "product-container"
      const image_url = `${apiBasePath}/webshop/image/${item.image_id || 0}`;
      li.innerHTML = `
        <div class="product-image-container">
          <a href="product/${item.id}">
            <img src="${image_url}" alt="${item.name}">
          </a>
        </div>
        <div id="product-${item.id}" class="product">
          <div class="product-line">
            <a class="product-title" href="product/${item.id}">${item.name}</a>
            <span class="product-price">${price} ${Cart.currency}/${baseStr}</span>
          </div>
          <div class="product-input product-line">
            <input type="number" min=0 max=9999 step=${item.smallest_multiple} placeholder="0" class="product-amount"/>
            <span class="product-unit">${item.unit}</span>
            <button type="button" class="number-add uk-button uk-button-small uk-button-primary" data-amount="1">+</button>
          </div>
        </div>`;

      id2element.set(item.id, li);
      id2item.set(item.id, item);

      const productAmount = li.querySelector<HTMLInputElement>(".product-amount")!;
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

      li.querySelector(".number-add")!.addEventListener("click", ev => {
        productAmount.value = "" + (Number(productAmount.value) + Number((<HTMLElement>ev.currentTarget).getAttribute("data-amount")));
        // Ugly
        productAmount.onchange!(null as unknown as Event);
        ev.preventDefault();
      });

      item.parentList = productListLi;
      productListLi.appendChild(li);
    }
    productListElem.appendChild(productListLi);
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

    common.updateCartSum(cart, id2item);
  }

  setLoggedIn(localStorage.getItem("token") !== undefined && localStorage.getItem("token") !== null);
  common.refreshLoggedIn((loggedIn, permissions) => {
    setLoggedIn(loggedIn);
  });
  refreshUIFromCart(Cart.fromStorage());

  document.querySelector("#product-search-field")!.addEventListener("input", ev => {
    const allItems = [];
    for (const item of id2item.values()) allItems.push(item);
    const matchingItems = shopsearch.search(allItems, (<HTMLInputElement>ev.currentTarget).value);

    for (const item of allItems) {
      const elem = id2element.get(item.id)!;
      elem.remove();
    }

    for (const item of matchingItems) {
      const elem = id2element.get(item.id);
      item.parentList.appendChild(elem);
    }
  });
});