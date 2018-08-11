import * as common from "./common"
import Cart from "./cart"
declare var UIkit: any;

document.addEventListener('DOMContentLoaded', () => {
    const apiBasePath = window.apiBasePath;

    const updateUnit = () => {
        const unit = (<HTMLInputElement>document.querySelector("#unit")).value;
        document.querySelector("#price-unit").innerHTML = Cart.currency + "/" + unit;
        document.querySelector("#multiple-unit").innerHTML = unit;
    };

    document.querySelector("#unit").addEventListener("input", ev => updateUnit());
    updateUnit();

    const data = JSON.parse(document.querySelector("#action-data").textContent);
    const action_categories = data.action_categories;
    let deletedActionIDs : (number|string)[] = [];

    function add_action(action: any) {
        let options = "";
        for (const cat of action_categories) {
            options += `<option value="${ cat.id }" ${ action.action_id == cat.id ? "selected" : "" }>${cat.name}</option>`;
        }


        const wrapper = document.createElement('div');
        wrapper.innerHTML =
            `<div data-id="${ action.id }" class="product-action uk-flex uk-margin">
                <select required class="uk-select uk-margin-right">
                    ${options}
                </select>
                <input required class="uk-input uk-margin-right" type="number" value="${ action.value }" />
                <button type="button" class="uk-button uk-button-danger uk-button-small" uk-icon="trash"></button>
            </div>`;
        const element = <HTMLElement>wrapper.firstChild;

        element.querySelector("button").addEventListener("click", ev => {
            ev.preventDefault();
            // Note that the ID may change from its original value.
            // In particular new actions start out with an id of 'new' which is later changed when the action is saved.
            deletedActionIDs.push(Number(element.getAttribute("data-id")));
            element.remove();
        });

        document.querySelector("#action-list").appendChild(element);
    }

    for (const action of data.actions) {
        add_action(action);
    }

    let isSaving = false;

    document.querySelector("#product-cancel").addEventListener("click", ev => {
        ev.preventDefault();
        // Redirect the user back to the webshop
        window.location.href = "/shop#edit";
    });

    // Wow: So much code!
    // Should probably simplify this...
    document.querySelector(".product-edit-form").addEventListener("submit", ev => {
        ev.preventDefault();
        if (isSaving) return;

        let id = (<HTMLInputElement>document.querySelector("#product-id")).value;
        const type = id == "new" ? "POST" : "PUT";
        const url = apiBasePath + "/webshop/product" + (id == "new" ? "" : "/" + id);
        const spinner = document.querySelector(".progress-spinner");
        spinner.classList.add("progress-spinner-visible");

        common.ajax(type, url, {
            id: id,
            name: common.getValue("#name"),
            category_id: common.getValue("#category"),
            description: common.getValue("#description"),
            price: common.getValue("#price"),
            unit: common.getValue("#unit"),
            smallest_multiple: common.getValue("#smallest_multiple"),
            filter: common.getValue("#filter"),
        }).then(json => {
            if (id == "new") {
                // Update the form with the created product id
                id = json.data.id;
                (<HTMLInputElement>document.querySelector("#product-id")).value = "" + id;
                history.replaceState(history.state, "Edit Product", id + "/edit");
            }

            const futures : Promise<any>[] = [];
            [].forEach.call(document.querySelectorAll(".product-action"), (element: HTMLElement) => {
                const id2 = element.getAttribute("data-id");
                const value = element.querySelector("input").value;
                const actionID = element.querySelector("select").value;

                const type2 = id2 == "new" ? "POST" : "PUT";
                const url2 = apiBasePath + "/webshop/product_action" + (id2 == "new" ? "" : "/" + id2);
                const future = common.ajax(type2, url2, {
                    id: id2,
                    product_id: id,
                    action_id: actionID,
                    value: value
                });
                futures.push(future);

                future.then(json => {
                    if (id2 == "new") {
                        // Update the form with the action id
                        element.setAttribute("data-id", json.data.id);
                    }
                    // UIkit.modal.alert("Saved action");
                }).catch (json => {
                    if (json.message == "Unauthorized") {
                        UIkit.modal.alert("<h2>Failed to save action</h2>You are not logged in");
                    } else {
                        UIkit.modal.alert("<h2>Failed to save action</h2>" + common.get_error(json));
                    }
                });
            });

            for (const id2 of deletedActionIDs) {
                if (id2 !== "new") {
                    const url2 = apiBasePath + "/webshop/product_action/" + id2;
                    const future = common.ajax("DELETE", url2, {});
                    futures.push(future);

                    future.catch(json => {
                        if (json.message == "Unauthorized") {
                            UIkit.modal.alert("<h2>Failed to delete action</h2>You are not logged in");
                        } else {
                            UIkit.modal.alert("<h2>Failed to delete action</h2>" + common.get_error(json));
                        }
                    });
                }
            }
            deletedActionIDs = [];

            Promise.all(futures).then(() => {
                // Redirect the user back to the webshop
                window.location.href = "/shop#edit";
            }).catch(() => {
                isSaving = false;
                // UIkit.modal.alert("Saved");
                spinner.classList.remove("progress-spinner-visible");
            });
        }).catch(json => {
            isSaving = false;
            spinner.classList.remove("progress-spinner-visible");
            if (json.message == "Unauthorized") {
                UIkit.modal.alert("<h2>Failed to save product</h2>You are not logged in");
            } else {
                UIkit.modal.alert("<h2>Failed to save product</h2>" + common.get_error(json));
            }
        });
    });

    document.querySelector("#add-action").addEventListener("click", ev => {
        ev.preventDefault();
        new UIkit.modal('#add-action-modal').hide();

        add_action({
            id: "new",
            action_id: common.getValue("#add-action-category"),
            value: 0,
        });
    });
});