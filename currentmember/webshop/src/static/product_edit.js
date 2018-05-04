$(document).ready(() => {
    let apiBasePath = "http://" + window.location.hostname + ":8010";
    let currency = "kr";

    $("#unit").on("input change", ev => {
        $("#price-unit").html(currency + "/" + $(ev.currentTarget).val());
    });
    $("#unit").change();


    let done = true;

    $(".product-edit-form").submit(ev => {
        if (!done) return;

        ev.preventDefault();
        id = $("#product-id").val();
        const type = id == "new" ? "POST" : "PUT";
        const url = apiBasePath + "/webshop/product" + (id == "new" ? "" : "/" + id)

        $.ajax({
            type: type,
            url: url,
            data: JSON.stringify({
                id: id,
                name: $("#name").val(),
                category_id: $("#category").val(),
                description: $("#description").val(),
                price: $("#price").val(),
                unit: $("#unit").val(),
            }),
            contentType: "application/json; charset=utf-8",
            dataType: "json",
            headers: {
            "Authorization": "Bearer " + localStorage.token
        }
        }).done((data, textStatus, xhr) => {
            done = true;
            if (id == "new") {
                // Update the form with the created product id
                id = xhr.responseJSON.data.id;
                $("#product-id").val(id);
                history.replaceState(history.state, "Edit Product", id + "/edit");
            }
            UIkit.modal.alert("Saved");
        }).fail((xhr, textStatus, error) => {
            done = true;
            if (xhr.responseJSON.message == "Unauthorized") {
                UIkit.modal.alert("<h2>Failed to save product</h2>You are not logged in");
            } else {
                UIkit.modal.alert("<h2>Failed to save product</h2>" + xhr.responseJSON.status);
            }
        });
    });
});