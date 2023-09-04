import { useEffect, useState } from "preact/hooks";
import { Product } from "./payment_common";

export interface Item {
	id: number;
	count: number;
}

export default class Cart {
	items: Item[];

	constructor(items: Item[]) {
		this.items = items;
	}

	static readonly currency = "kr";
	static readonly currencyDecimals = 2;

	static formatCurrency(value: number): string {
		return value.toFixed(Cart.currencyDecimals) + " kr";
	}

	// Keep local storage in sync even though other tabs change it
	static startLocalStorageSync(onSync: (cart: Cart) => void) {
		const onStorage = (e: StorageEvent) => {
			if (e.oldValue !== e.newValue) {
				localStorage.setItem(e.key!, e.newValue!);
				onSync(Cart.fromStorage());
			}
		};

		// When using the back button to navigate back
		// many browsers do not actually reload the page, but simply restore it from memory
		// In this case we need to do some refreshing to ensure that for example the shopping cart is up to date
		const onPageShow = (persisted: PageTransitionEvent) => {
			onSync(Cart.fromStorage());
		};

		window.addEventListener('storage', onStorage);
		window.addEventListener("pageshow", onPageShow);

		return () => {
			window.removeEventListener('storage', onStorage);
			window.removeEventListener("pageshow", onPageShow);
		}
	}

	setItem(productID: number, count: number) {
		let done = false;

		for (let i = 0; i < this.items.length; i++) {
			if (this.items[i].id == productID) {
				if (count == 0) {
					this.items.splice(i, 1);
				} else {
					this.items[i].count = count;
				}
				done = true;
				break;
			}
		}

		if (!done && count > 0) {
			this.items.push({
				id: productID,
				count: count,
			});
		}
	}

	getItemCount(productID: number): number {
		for (let i = 0; i < this.items.length; i++) {
			if (this.items[i].id == productID) return this.items[i].count;
		}
		return 0;
	}

	sum(id2product: Map<number, any>) {
		let totalSum = 0;
		this.items = this.items.filter(i => id2product.get(i.id))
		for (let item of this.items) {
			totalSum += item.count * id2product.get(item.id).price;
		}
		return totalSum;
	}

	static adjustItemCount(count: number, item: any): number {
		if (count < 0) count = 0;
		// Note: the |0 will ensure the number is a 32-bit integer
		return (Math.ceil(count / item.smallest_multiple) * item.smallest_multiple) | 0;
	}

	saveToStorage() {
		localStorage.setItem("cart", JSON.stringify(this.items));
	}

	static oneOfEachProduct(products: Product[]) {
		return new Cart(products.map(p => ({ id: p.id, count: 1 })))
	}

	static fromStorage(): Cart {
		let cart = [];
		try {
			cart = JSON.parse(localStorage.getItem("cart")!);
		} catch (e) { }

		if (!Array.isArray(cart)) {
			cart = [];
		}
		return new Cart(cart);
	}
}

export const useCart = () => {
	// Keep local storage in sync even though other tabs change it
	const [cart, setCart] = useState(Cart.fromStorage());
	useEffect(() => Cart.startLocalStorageSync(setCart));
	return {
		cart, setCart: (cart: Cart) => {
			cart.saveToStorage();
			setCart(Cart.fromStorage());
		}
	};
}
