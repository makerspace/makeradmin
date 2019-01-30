export function renderSidebarCategories(categories: any, is_shop_page: boolean = false) {
  const categoriesUl = document.getElementById("categories");
  const fixedLi = categoriesUl.firstChild;
  categories.forEach((category: any) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <a href="/shop/#category${category.id}" ${is_shop_page==true ? 'uk-scroll': ''}><span uk-icon="tag"></span> ${category.name}</a>
      <div class="category-edit-box">
        <button data-id="${category.id}" data-name="${category.name}" class="category-edit edit uk-button uk-button-primary uk-button-small" uk-icon="pencil"/>
        <button data-id="${category.id}" class="category-delete edit uk-button uk-button-danger uk-button-small" uk-icon="trash"/>
      </div>`;
    categoriesUl.insertBefore(li, fixedLi);
  });
}
