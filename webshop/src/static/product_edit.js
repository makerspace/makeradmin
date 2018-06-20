$(document).ready(() => {
    const apiBasePath = window.apiBasePath;
    const currency = "kr";

    $("#unit").on("input change", ev => {
        $("#price-unit").html(currency + "/" + $(ev.currentTarget).val());
        $("#multiple-unit").html($(ev.currentTarget).val());
    });
    $("#unit").change();

    const data = JSON.parse($("#action-data")[0].textContent);
    const action_categories = data.action_categories;
    let deletedActionIDs = [];

    function add_action(action) {
        options = ""
        for (const cat of action_categories) {
            options += `<option value="${ cat.id }" ${ action.action_id == cat.id ? "selected" : "" }>${cat.name}</option>`;
        }

        const element = $(
            `<div data-id="${ action.id }" class="product-action uk-flex uk-margin">
                <select required class="uk-select uk-margin-right">
                    ${options}
                </select>
                <input required class="uk-input uk-margin-right" type="number" value="${ action.value }" />
                <button type="button" class="uk-button uk-button-danger uk-button-small" uk-icon="trash"></button>
            </div>`
        );

        $(element).find("button").click(ev => {
            ev.preventDefault();
            // Note that the ID may change from its original value.
            // In particular new actions start out with an id of 'new' which is later changed when the action is saved.
            deletedActionIDs.push($(element).attr("data-id"));
            $(element).remove();
        });

        $("#action-list").append(element);
    }

    for (const action of data.actions) {
        add_action(action);
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

    let isSaving = false;
    // Wow: So much code!
    // Should probably simplify this...
    $(".product-edit-form").submit(ev => {
        ev.preventDefault();
        if (isSaving) return;

        id = $("#product-id").val();
        const type = id == "new" ? "POST" : "PUT";
        const url = apiBasePath + "/webshop/product" + (id == "new" ? "" : "/" + id);
        $(".progress-spinner").toggleClass("progress-spinner-visible", true);

        ajax(type, url, {
            id: id,
            name: $("#name").val(),
            category_id: $("#category").val(),
            description: $("#description").val(),
            price: $("#price").val(),
            unit: $("#unit").val(),
            smallest_multiple: $("#smallest_multiple").val(),
        }).done((data, textStatus, xhr) => {
            if (id == "new") {
                // Update the form with the created product id
                id = xhr.responseJSON.data.id;
                $("#product-id").val(id);
                history.replaceState(history.state, "Edit Product", id + "/edit");
            }

            const futures = [];
            for (const element of $(".product-action")) {
                const id2 = $(element).attr("data-id");
                const value = $(element).find("input").val();
                const actionID = $(element).find("select").val();

                const type2 = id2 == "new" ? "POST" : "PUT";
                const url2 = apiBasePath + "/webshop/product_action" + (id2 == "new" ? "" : "/" + id2);
                const future = ajax(type2, url2, {
                    id: id2,
                    product_id: id,
                    action_id: actionID,
                    value: value
                });
                futures.push(future);

                future.done((data, textStatus, xhr) => {
                    if (id2 == "new") {
                        // Update the form with the action id
                        $(element).attr("data-id", xhr.responseJSON.data.id);
                    }
                    // UIkit.modal.alert("Saved action");
                }).fail((xhr, textStatus, error) => {
                    if (xhr.responseJSON.message == "Unauthorized") {
                        UIkit.modal.alert("<h2>Failed to save action</h2>You are not logged in");
                    } else {
                        UIkit.modal.alert("<h2>Failed to save action</h2>" + xhr.responseJSON.status);
                    }
                });
            }

            for (const id2 of deletedActionIDs) {
                if (id2 !== "new") {
                    const url2 = apiBasePath + "/webshop/product_action/" + id2;
                    const future = ajax("DELETE", url2, {});
                    futures.push(future);

                    future.fail((xhr, textStatus, error) => {
                        if (xhr.responseJSON.message == "Unauthorized") {
                            UIkit.modal.alert("<h2>Failed to delete action</h2>You are not logged in");
                        } else {
                            UIkit.modal.alert("<h2>Failed to delete action</h2>" + xhr.responseJSON.status);
                        }
                    });
                }
            }
            deletedActionIDs = [];

            $.when.apply($,futures).fail(() => {
                isSaving = false;
                // UIkit.modal.alert("Saved");
                $(".progress-spinner").toggleClass("progress-spinner-visible", false);
            }).done(() => {
                // Redirect the user back to the webshop
                window.location.href = "/shop#edit";
            });
        }).fail((xhr, textStatus, error) => {
            isSaving = false;
            $(".progress-spinner").toggleClass("progress-spinner-visible", false);
            if (xhr.responseJSON.message == "Unauthorized") {
                UIkit.modal.alert("<h2>Failed to save product</h2>You are not logged in");
            } else {
                UIkit.modal.alert("<h2>Failed to save product</h2>" + xhr.responseJSON.status);
            }
        });
    });

    $("#add-action").click(ev => {
        ev.preventDefault();
        new UIkit.modal('#add-action-modal').hide();

        add_action({
            id: "new",
            action_id: $("#add-action-category").val(),
            value: 0,
        });
    });
});