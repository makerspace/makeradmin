import React from "react";
import { matchPath, useLocation } from "react-router";
import { Link, NavLink } from "react-router-dom";
import * as _ from "underscore";
import Icon from "./Components/icons";

export const NavItem = (props) => {
    const { icon, to } = props;
    const location = useLocation();

    return (
        <li className={location.pathname.indexOf(to) >= 0 ? "uk-active" : ""}>
            <NavLink to={to}>
                {icon ? (
                    <>
                        <Icon icon={icon} />
                        &nbsp;
                    </>
                ) : null}
                <span>{props.children}</span>
            </NavLink>
        </li>
    );
};

export const Nav = ({ nav: { brand, items } }) => (
    <nav className="uk-navbar-container">
        <div className="uk-navbar-left">
            <Link to="/" className="uk-navbar-item uk-logo">
                {brand}
            </Link>
            {/* The uk-flex-wrap is added to make the items not overflow. Feels like a hack. */}
            <ul className="uk-navbar-nav uk-flex-wrap">
                {items.map((item, i) => (
                    <NavItem to={item.target} icon={item.icon} key={i}>
                        {item.text}
                    </NavItem>
                ))}
            </ul>
        </div>
    </nav>
);

export const SideNav = ({ nav }) => {
    const location = useLocation();
    let activeItem = _.find(
        nav.items,
        (i) => matchPath(location.pathname, i.target) !== null,
    );

    if (!activeItem || _.isUndefined(activeItem.children)) {
        return null;
    }

    return (
        <div
            className="uk-panel uk-panel-box"
            style={{ marginBottom: "1em" }}
            data-uk-sticky="{top:35}"
        >
            <ul
                className="uk-nav uk-nav-default"
                data-uk-scrollspy-nav="{closest:'li', smoothscroll:true}"
            >
                <li className="uk-nav-header">{activeItem.text}</li>
                <li className="uk-nav-divider" />
                {activeItem.children.map((item, i) => {
                    if (item.type === "separator") {
                        return <li key={i} className="uk-nav-divider" />;
                    }

                    if (item.type === "heading") {
                        return (
                            <li key={i} className="uk-nav-header">
                                {item.text}
                            </li>
                        );
                    }

                    return (
                        <NavItem
                            key={i}
                            to={item.target}
                            icon={item.icon}
                            activeItem={activeItem}
                        >
                            {item.text}
                        </NavItem>
                    );
                })}
            </ul>
        </div>
    );
};
