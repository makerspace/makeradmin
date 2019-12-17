/// <reference path="../node_modules/moment/moment.d.ts" />
import * as common from "./common"
//import * as moment from 'moment';
import 'moment/locale/sv';

declare var UIkit: any;
declare var moment: any;
declare var Chart: any;

common.documentLoaded().then(() => {
	const apiBasePath = window.apiBasePath;
	const webshop_edit_permission = "webshop_edit";
	const service_permission = "service";

	const root = document.getElementById("single-page-content");

	const future1 = common.ajax("GET", apiBasePath + "/statistics/membership/by_date", null);
	const future2 = common.ajax("GET", apiBasePath + "/statistics/lasertime/by_month", null);

	Promise.all([future1, future2]).then(data => {
		const membershipjson = data[0];
		const laserjson = data[1];
		addChart(root, membershipjson.data);
		addLaserChart(root, laserjson.data);
		addRandomCharts(root);
	})
	.catch(json => {
		UIkit.modal.alert("<h2>Couldn't load statistics</h2>" + json.message + " " + json.error);
	});
});

const colors = [
	"#e41a1c",
	"#377eb8",
	"#4daf4a",
	"#984ea3",
	"#ff7f00",
	"#ffff33",
]

var timeFormat = 'YYYY-MM-DD HH:mm';

function splitSeries (items: Array<any>) {
	const dates = [];
	const values = [];
	for (let i = 0; i < items.length; i++) {
		dates.push(new Date(items[i][0]));
		values.push(items[i][1]);
	}
	return { dates: dates, values: values };
}

function toPoints (items: Array<any>) {
	const values = [];
	for (let i = 0; i < items.length; i++) {
		values.push({ x: new Date(items[i][0]), y: items[i][1] });
	}
	return values;
}

function filterDuplicates(items: Array<any>) {
	const newValues = [];
	for (let i = 0; i < items.length; i++) {
		if (i == 0 || items[i].x != items[i-1].x) {
			newValues.push(items[i]);
		}
	}
	return newValues;
}

function maxOfSeries(items: Array<any>) {
	let mx = null;
	for (let i = 0; i < items.length; i++) {
		if (mx == null || items[i].y > mx.y) {
			mx = items[i];
		}
	}
	return mx;
}

function date2str(date: String|Date) {
	if (date instanceof Date) return date.toISOString().split('T')[0];
	else return date;
}

function pointAtDate(items: Array<any>, date: Date) {
	let best = null;
	for (let i = 0; i < items.length; i++) {
		if (best == null || items[i].x <= date) {
			best = items[i];
		}
	}
	return best;
}

function addChart(root: HTMLElement, data: any) {
	// lab = splitSeries(data.labmembership);
	// member = splitSeries(data.membership);
	const dataMembership = filterDuplicates(toPoints(data.membership));
	const dataLabaccess = filterDuplicates(toPoints(data.labaccess));
	const maxtime = new Date();

	const config = {
		type: 'line',
		data: {
			datasets: [{
				label: 'Föreningsmedlemmar',
				backgroundColor: "#FF000077",
				borderColor: colors[0],
				fill: false,
				data: dataMembership
			},
			{
				label: 'Labmedlemmar',
				backgroundColor: "#0000FF77",
				borderColor: colors[1],
				fill: false,
				data: dataLabaccess
			}
			],
		},
		options: {
			responsive: true,
			elements: {
				line: {
					tension: 0,
				},
				point:{
					radius: 1,
					hoverRadius: 3,
				}
			},
			tooltips: {
				mode: 'nearest',
				intersect: false,
			},
			title: {
				display: true,
				text: 'Medlemsskap'
			},
			scales: {
				xAxes: [{
					type: 'time',
					time: {
						parser: timeFormat,
						// round: 'day'
						tooltipFormat: 'll',
						max: maxtime,
					},
					scaleLabel: {
						display: true,
						labelString: 'Datum'
					}
				}],
				yAxes: [{
					ticks: {
						min: 0
					},
					scaleLabel: {
						display: true,
						labelString: 'Antal'
					}
				}]
			},
			pan: {
				enabled: true,
				mode: 'x',
			},
			zoom: {
				enabled: true,
				mode: 'x',
			},
		}
	};


	const memberstats = <HTMLDivElement>document.createElement("div");
	const highestMembership = maxOfSeries(dataMembership) || { x: "never", y: 0};
	const highestLabaccess = maxOfSeries(dataLabaccess) || { x: "never", y: 0};

	const today = new Date();
	const currentMembership = pointAtDate(dataMembership, today) || { x: today, y: 0};
	const currentLabaccess = pointAtDate(dataLabaccess, today) || { x: today, y: 0};

	memberstats.innerHTML = `
	<canvas width=500 height=300></canvas>
	<div class="statistics-member-stats-box">
	<div class="statistics-member-stats-row"><span class="statistics-member-stats-type">Membership</span><span  class="statistics-member-stats-value">${currentMembership.y}</span></div>
	<div class="statistics-member-stats-row"><span class="statistics-member-stats-type">Membership record</span><span  class="statistics-member-stats-value">${highestMembership.y} members on ${date2str(highestMembership.x)}</span></div>
	<div class="statistics-member-stats-row"><span class="statistics-member-stats-type">Labaccess</span><span  class="statistics-member-stats-value">${currentLabaccess.y}</span></div>
	<div class="statistics-member-stats-row"><span class="statistics-member-stats-type">Labaccess record</span><span  class="statistics-member-stats-value">${highestLabaccess.y} members on ${date2str(highestLabaccess.x)}</span></div>
	</div>
	`;
	memberstats.className = "statistics-member-stats";

	const canvas = memberstats.querySelector("canvas"); // <HTMLCanvasElement>document.createElement("canvas");
	const ctx = canvas.getContext('2d');
	const chart = new Chart(ctx, config);

	root.appendChild(memberstats);
}

function addRandomCharts(root: HTMLElement) {
	{
		const canvas = <HTMLCanvasElement>document.createElement("canvas");
		root.appendChild(canvas);
		canvas.width = 500;
		canvas.height = 300;
		const ctx = canvas.getContext('2d');

		// And for a doughnut chart
		const myDoughnutChart = new Chart(ctx, {
			type: 'doughnut',
			data: {
				datasets: [{
					"data": [0.1, 0.9],
					"backgroundColor": [
						colors[1],
						colors[0],
					]
				}],
				labels: [
					"Tid som du är på makerspace",
					"Annan tid som borde spenderas på makerspace",
				]
			},
			options: {
				title: {
					display: true,
					text: 'Motiverande fake-data'
				},
				legend: {
					position: 'top',
				}
			}
		});
	}
}

function addLaserChart(root: HTMLElement, data: any) {
	// lab = splitSeries(data.labmembership);
	// member = splitSeries(data.membership);
	const maxtime = new Date();

	const config = {
		type: 'bar',
		data: {
			datasets: [{
				label: 'Laserminuter',
				backgroundColor: "#FF000077",
				borderColor: colors[0],
				fill: false,
				data: toPoints(data),
				steppedLine: true,
			},
			],
		},
		options: {
			title: {
				display: true,
				text: 'Användning av laserskäraren',
			},
			scales: {
				xAxes: [{
					type: 'time',
					time: {
						parser: 'YYYY-MM',
						// round: 'month'
						tooltipFormat: 'll',
						unit: 'month',
						max: maxtime,
					},
					scaleLabel: {
						display: true,
						labelString: 'Datum'
					}
				}],
				yAxes: [{
					ticks: {
						min: 0
					},
					scaleLabel: {
						display: true,
						labelString: 'Antal'
					}
				}]
			},
		}
	};

	const canvas = <HTMLCanvasElement>document.createElement("canvas");
	root.appendChild(canvas);
	canvas.width = 500;
	canvas.height = 300;
	const ctx = canvas.getContext('2d');
	const chart = new Chart(ctx, config);
}
 