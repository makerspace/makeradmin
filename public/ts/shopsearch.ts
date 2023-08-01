import { Product } from "./payment_common";

export function search(items: Product[], query: string) {
	query = query.toLowerCase().trim();
	if (query === "") {
		return items;
	}

	const keys = query.split(" ");
	const scores = [];
	for (const item of items) {
		const nameKeys = item.name.toLowerCase().trim().split(" ");
		const descKeys = item.description.toLowerCase().trim().split(" ");

		let score = 0;
		for (const queryKey of keys) {
			let matches = 0;
			for (const itemKey of nameKeys) {
				if (itemKey.includes(queryKey)) {
					matches = Math.max(matches, 1);
				}
				if (itemKey === queryKey) {
					matches = Math.max(matches, 2);
				}
			}

			for (const itemKey of descKeys) {
				if (itemKey.includes(queryKey)) {
					matches += 0.1;
				}
			}

			score += matches;
		}

		if (score > 0) {
			scores.push({ score: score, item: item });
		}
	}

	scores.sort((a, b) => b.score - a.score);

	items = [];
	for (const item of scores) {
		items.push(item.item);
	}

	return items;
}