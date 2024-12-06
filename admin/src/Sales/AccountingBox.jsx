import React from "react";
import { NavItem } from "../nav";

export default function AccountingBox({ children }) {
    return (
        <div>
            <h2>Bokföring</h2>

            <ul className="uk-tab">
                <NavItem to={"/sales/accounting/exporting"}>Exportera</NavItem>
                <NavItem to={"/sales/accounting/overview-product"}>
                    Produkter
                </NavItem>
                <NavItem to={"/sales/accounting/account"}>Konton</NavItem>
                <NavItem to={"/sales/accounting/cost-center"}>
                    Kostnadsställen
                </NavItem>
            </ul>

            {children}
        </div>
    );
}
