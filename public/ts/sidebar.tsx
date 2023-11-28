import { useEffect, useRef, useState } from "preact/hooks";
import { ComponentChildren} from "preact";
import { logout } from "./common";
import Cart from "./cart";
import { Product, ProductData } from "./payment_common";

const NavItem = ({ url, icon, children }: { url: string, icon: string, children: ComponentChildren }) => {
    let path = location.pathname.trim();
    if (path.endsWith("/")) {
        path = path.substring(0, path.length - 1);
    }

    return <li className={url === path ? "active" : ""}>
        <a href={url}><span uk-icon={icon}></span> {children}</a>
    </li>
}

export const Sidebar = ({ cart, className = "" }: { cart: { cart: Cart, productData: ProductData } | null, className?: string }) => {
    const sidebarRef = useRef<HTMLDivElement>(null);
    const [isSidebarScrollable, setIsSidebarScrollable] = useState(false);

    useEffect((): (() => void) => {
        const checkSidebarHeight = () => {
            if(sidebarRef.current) {
                setIsSidebarScrollable(sidebarRef.current.scrollHeight > sidebarRef.current.clientHeight);
            }
        }
        checkSidebarHeight();
        window.addEventListener("resize", checkSidebarHeight);

        return () => {
            window.removeEventListener("resize", checkSidebarHeight);
        };
    }, []);

    let path = location.pathname.trim();
    if (path.endsWith("/")) {
        path = path.substring(0, path.length - 1);
    }
    return <div id="left-sidebar" ref={sidebarRef} className={isSidebarScrollable ? "scrollable" : ""}>
        <div className={`sidebar-fixed-content ${className}`}>
            <img className="makerspace-logo" src={`${window.staticBasePath}/images/logo-transparent-500px-300x210.png`} />
            <ul className="uk-nav uk-nav-default">
                <NavItem url="/member" icon="user">Medlemsvy</NavItem>
                <NavItem url="/shop" icon="cart">Webshop</NavItem>
                {(path === "/shop" || path === "/shop/cart") && cart !== null &&
                    <ul id="categories" className="uk-nav-sub">
                        {cart.productData.categories.filter(category => category.items.filter(item => item.show).length > 0).map(category =>
                            <li><a href={`/shop/#category${category.id}`} uk-scroll={path === "/shop"}><span uk-icon="tag"></span> {category.name}</a></li>
                        )}
                        <NavItem url="/shop/cart" icon="cart">Min Kundvagn ({Cart.formatCurrency(cart.cart.sum(cart.productData.id2item))})</NavItem>
                    </ul>
                }
                <NavItem url="/shop/member/history" icon="history">Min köphistorik</NavItem>
                <NavItem url="/shop/member/courses" icon="star">Kurser</NavItem>
                <NavItem url="/shop/member/licenses" icon="tag">Licenser och rabatter</NavItem>
                {/*<NavItem url="#" icon="cart">Presentkort</NavItem>*/}
                <li>
                    <a onClick={e => {
                        e.preventDefault();
                        logout();
                    }}><span uk-icon="sign-out"></span> Logga ut</a>
                </li>

                {cart !== null &&
                    <li className={`uk-button uk-button-primary sidebar-buy-btn ${cart.cart.items.length === 0 ? 'cart-empty' : ''}`}>
                        <a href="/shop/cart"><span uk-icon="cart"></span> Betala
                            <span id="cart-sum">{Cart.formatCurrency(cart.cart.sum(cart.productData.id2item))}</span>
                        </a>
                    </li>
                }
            </ul>
        </div>
    </div>
}
