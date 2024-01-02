export function renderSidebarCategories(
    productData: any,
    is_shop_page: boolean = false,
) {
    const categoriesUl = document.getElementById("categories")!;
    const fixedLi = categoriesUl.firstChild;
    productData.forEach((category: any) => {
        const li = document.createElement("li");
        li.innerHTML = `
      <a href="/shop/#category${category.id}" ${
          is_shop_page == true ? "uk-scroll" : ""
      }><span uk-icon="tag"></span> ${category.name}</a>
    `;
        categoriesUl.insertBefore(li, fixedLi);
    });
}
