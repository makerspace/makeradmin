import Cart, { useCart } from "./cart";
import * as shopsearch from "./shopsearch";
import * as common from "./common";
import * as login from "./login"
import { renderSidebarCategories } from "./category";
import { LoadProductData, Product, ProductCategory, ProductData } from "./payment_common";
import { useEffect, useState } from "preact/hooks";
import { Sidebar } from "./sidebar";
import { render } from "preact";
import { LoadCurrentMemberInfo } from "./member_common";
declare var UIkit: any;

const ProductCategoryHeader = ({ category }: { category: ProductCategory }) => {
  return <li><h3 id={`category${category.id}`}>{category.name}</h3></li>
}

const ProductItem = ({ item, cart, onChangeCart }: { item: Product, cart: Cart, onChangeCart: (cart: Cart)=>void }) => {
  const price = Number(item.price) * item.smallest_multiple;

  let baseStr = item.smallest_multiple > 1 ? item.smallest_multiple + item.unit : item.unit;

  const li = document.createElement("div");
  li.className = "product-container"
  const image_url = `${window.apiBasePath}/webshop/image/${item.image_id || 0}`;
  const count = cart.getItemCount(item.id);

  return <div className="product-container">
      <div class="product-image-container">
        <a href={`product/${item.id}`}>
          <img src={image_url} alt={item.name} />
        </a>
      </div>
      <div id={`product-${item.id}`} class="product">
        <div class="product-line">
          <a class="product-title" href={`product/${item.id}`}>{item.name}</a>
          <span class="product-price">{price} {Cart.currency}/{baseStr}</span>
        </div>
        <div class="product-input product-line">
          <input type="number" min={0} max={9999} step={item.smallest_multiple} placeholder="0" value={count > 0 ? "" + count : ""} class="product-amount" onClick={e => {
            // Select everything in the textfield when clicking on it
            e.currentTarget.select()
          }}
          onInput={e => {
            let newAmount = Cart.adjustItemCount(Number(e.currentTarget.value), item);
            cart.setItem(item.id, newAmount);
            onChangeCart(cart);
          }}
          onChange={e => {
            let newAmount = Cart.adjustItemCount(Number(e.currentTarget.value), item);
            cart.setItem(item.id, newAmount);
            onChangeCart(cart);
          }}
          />
          <span class="product-unit">{item.unit}</span>
          <button type="button" class="number-add uk-button uk-button-small uk-button-primary" data-amount="1"
            onClick={e => {
              cart.setItem(item.id, cart.getItemCount(item.id) + 1);
              onChangeCart(cart);
              e.preventDefault();
            }}
          >+</button>
        </div>
      </div>
    </div>;
}

const ProductCategory = ({ category, cart, onChangeCart, visibleItems }: { category: ProductCategory, cart: Cart, onChangeCart: (cart: Cart)=>void, visibleItems: Set<number> }) => {
  const anyVisible = category.items.some(item => visibleItems.has(item.id));
  if (!anyVisible) {
    return null;
  }

  return <>
    <ProductCategoryHeader category={category} />
    <li className="product-container-list">
      {category.items.filter(item => visibleItems.has(item.id)).map(item => <ProductItem item={item} cart={cart} onChangeCart={onChangeCart} />)}
    </li>
  </>
}

const SearchField = ({ id2item, onChangeVisibleItems }: { id2item: Map<number, Product>, onChangeVisibleItems: (visible: Set<number>)=>void }) => {
  return <form className="product-search uk-search uk-search-default">
    <span uk-search-icon></span>
    <input
      className="uk-search-input"
      id="product-search-field"
      type="search"
      placeholder="Hitta produkt..."
      onInput={e => {
        const allItems = [];
        for (const item of id2item.values()) allItems.push(item);
        const matchingItems = shopsearch.search(allItems, (e.currentTarget as HTMLInputElement).value);
        return onChangeVisibleItems(new Set(matchingItems.map(item => item.id)));
      }}
    />
  </form>
}
const ShopPage = ({ productData }: { productData: ProductData }) => {
  const { cart, setCart } = useCart();
  const [visibleItems, setVisibleItems] = useState(new Set(productData.id2item.keys()));

  // Load saved layout mode
  const [layoutMode, setLayoutModeInternal] = useState(localStorage.getItem("webshop-layout-mode") || "layout-grid");
  const layoutModes = ["layout-grid", "layout-list", "layout-table"];
  function setLayoutMode(mode: string) {
    setLayoutModeInternal(mode);
    localStorage.setItem("webshop-layout-mode", mode);
  }
  if (!layoutModes.includes(layoutMode)) setLayoutMode(layoutModes[0]);

  return <>
      <Sidebar cart={{ cart, productData }} />
      <div id="content">
        <ul className={`product-list ${layoutMode}`}>
            <li className="product-search-bar">
                <SearchField id2item={productData.id2item} onChangeVisibleItems={setVisibleItems} />
                <div className="toggle-product-images uk-button-group">
                    <button className={`layout-button uk-icon-button ${layoutMode === "layout-grid" ? "selected" : ""}`} uk-icon="icon: grid" onClick={() => setLayoutMode("layout-grid")}></button>
                    <button className={`layout-button uk-icon-button ${layoutMode === "layout-list" ? "selected" : ""}`} uk-icon="icon: list" onClick={() => setLayoutMode("layout-list")}></button>
                    <button className={`layout-button uk-icon-button ${layoutMode === "layout-table" ? "selected" : ""}`} uk-icon="icon: table" onClick={() => setLayoutMode("layout-table")}></button>
                </div>
            </li>
            {productData.products.map(cat => <ProductCategory category={cat} cart={cart} onChangeCart={cart => {
              console.log("Setting cart to", cart);
              cart.saveToStorage();
              setCart(Cart.fromStorage());
            }} visibleItems={visibleItems} />)}
        </ul>
      </div>
    </>
}


common.documentLoaded().then(() => {
  const productData = LoadProductData();
  const member = LoadCurrentMemberInfo();
  const root = document.querySelector("#root") as HTMLElement;

  // renderSidebarCategories(productData, true);
  Promise.all([member, productData]).then(([member, productData]) => {
      if (root != null) {
          root.innerHTML = "";
          render(
              <ShopPage productData={productData} />,
              root
          );
      }
  })
      .catch(json => {
          // Probably Unauthorized, redirect to login page.
          if (json.status === common.UNAUTHORIZED) {
              // Render login
              login.render_login(root, null, null);
          } else {
              UIkit.modal.alert("<h2>Misslyckades med att hämta köphistorik</h2>" + common.get_error(json));
          }
      });
});
