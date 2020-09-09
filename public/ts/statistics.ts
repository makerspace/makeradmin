/// <reference path="../node_modules/moment/moment.d.ts" />
import * as common from "./common"
//import * as moment from 'moment';
import 'moment/locale/sv';

declare var UIkit: any;
declare var moment: any;
declare var Chart: any;

interface ServerResponse<T> {
	status: string,
	data: T,
}

common.documentLoaded().then(() => {
	const apiBasePath = window.apiBasePath;
	const webshop_edit_permission = "webshop_edit";
	const service_permission = "service";

	const root = document.getElementById("single-page-content")!;

	const future1 = common.ajax("GET", apiBasePath + "/statistics/membership/by_date", null);
	const future2 = common.ajax("GET", apiBasePath + "/statistics/lasertime/by_month", null);
	const future3 = common.ajax("GET", apiBasePath + "/quiz/statistics", null) as Promise<ServerResponse<QuizStatistics>>;

	Promise.all([future1, future2, future3]).then(data => {
		const membershipjson = data[0];
		const laserjson = data[1];
		addChart(root, membershipjson.data);
		addLaserChart(root, laserjson.data);
		addQuizChart(root, data[2].data)
		// addRandomCharts(root);
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

// const colors = [
// 	"#07719F",
// 	"#2785AD",
// 	"#9F7107",
// 	"#BE9A46",
// 	"#AD2727",
// 	"#BE4646",
// ]

var timeFormat = 'YYYY-MM-DD HH:mm';

function splitSeries(items: Array<any>) {
	const dates = [];
	const values = [];
	for (let i = 0; i < items.length; i++) {
		dates.push(new Date(items[i][0]));
		values.push(items[i][1]);
	}
	return { dates: dates, values: values };
}

function toPoints(items: Array<any>) {
	const values = [];
	for (let i = 0; i < items.length; i++) {
		values.push({ x: new Date(items[i][0]), y: items[i][1] });
	}
	return values;
}

function filterDuplicates(items: Array<any>) {
	const newValues = [];
	for (let i = 0; i < items.length; i++) {
		if (i == 0 || items[i].x != items[i - 1].x) {
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

function date2str(date: String | Date) {
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
				point: {
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
			annotation: {
				events: ["click"],
				annotations: [
					{
						drawTime: "afterDatasetsDraw",
						type: "line",
						mode: "vertical",
						scaleID: "x-axis-0",
						borderColor: "red",
						borderWidth: 1,
						value: maxtime
					}
				]
			}
		}
	};


	const memberstats = <HTMLDivElement>document.createElement("div");
	const highestMembership = maxOfSeries(dataMembership) || { x: "never", y: 0 };
	const highestLabaccess = maxOfSeries(dataLabaccess) || { x: "never", y: 0 };

	const today = new Date();
	const currentMembership = pointAtDate(dataMembership, today) || { x: today, y: 0 };
	const currentLabaccess = pointAtDate(dataLabaccess, today) || { x: today, y: 0 };

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

	const canvas = memberstats.querySelector("canvas")!; // <HTMLCanvasElement>document.createElement("canvas");
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

interface Question {
	question: string,
}

interface Option {
	correct: boolean,
	description: string,
}
interface OptionStatistics {
	answer_count: number,
	option: Option,
}

interface QuizStatistics {
	median_seconds_to_answer_quiz: number,
	answered_quiz_member_count: number,
	questions: {
		question: Question,
		options: OptionStatistics[],
		// Number of unique members that have answered this question
		member_answer_count: number,
		incorrect_answer_fraction: number,
	}[],
}

function addQuizChart(root: HTMLElement, data: QuizStatistics) {

	// Sort questions so that the more incorrectly answered questions are at the top
	data.questions.sort((a, b) => b.incorrect_answer_fraction - a.incorrect_answer_fraction);

	// Sort options so that the correct options are to the left.
	for (const q of data.questions) {
		q.options.sort((a, b) => {
			if (a.option.correct != b.option.correct) return a.option.correct ? 1 : 0;

			return b.answer_count - a.answer_count;
		});
	}

	// Maximum number of correct and incorrect alternatives for all questions
	const maxCorrect = data.questions.map(q => q.options.map<number>(o => o.option.correct ? 1 : 0).reduce((a, b) => a + b)).reduce((a, b) => Math.max(a, b));
	const maxIncorrect = data.questions.map(q => q.options.map<number>(o => o.option.correct ? 0 : 1).reduce((a, b) => a + b)).reduce((a, b) => Math.max(a, b));

	const correctColors = ["#23851E", "#289622"];
	const incorrectColors = ["#AD2727", "#C82D2D"];

	interface Dataset {
		label: string,
		backgroundColor: string,
		borderColor: string,
		data: any[],
		options: (null|OptionStatistics)[],
	}

	const incorrectDatasets: Dataset[] = [];
	const correctDatasets: Dataset[] = [];

	for (let i = 0; i < maxCorrect; i++) {
		let color = correctColors[Math.min(i, correctColors.length - 1)];
		correctDatasets.push({
			label: 'Korrekt',
			backgroundColor: color,
			borderColor: color,
			data: [],
			options: [],
		})
	}
	for (let i = 0; i < maxIncorrect; i++) {
		let color = incorrectColors[Math.min(i, incorrectColors.length - 1)];
		incorrectDatasets.push({
			label: 'Inkorrekt',
			backgroundColor: color,
			borderColor: color,
			data: [],
			options: [],
		})
	}

	const datasets = [...correctDatasets, ...incorrectDatasets];

	// Go through each question option and add values to the relevant datasets
	for (let qi = 0; qi < data.questions.length; qi++) {
		const q = data.questions[qi];
		let correct = 0;
		let incorrect = 0;

		for (const o of q.options) {
			let datasetIndex;
			let datasetArray;
			if (o.option.correct) {
				datasetIndex = correct;
				correct++;
				datasetArray = correctDatasets;
			} else {
				datasetIndex = incorrect;
				incorrect++;
				datasetArray = incorrectDatasets;
			}

			console.assert(datasetIndex < datasetArray.length);

			datasetArray[datasetIndex].data.push(o.answer_count / q.member_answer_count);
			datasetArray[datasetIndex].options.push(o);
		}

		// Ensure all datasets have the same length to ensure question indices are not messed up.
		for (let i = 0; i < datasets.length; i++) {
			if (datasets[i].data.length <= qi) {
				datasets[i].data.push(0);
				datasets[i].options.push(null);
			}
		}
	}

	const config = {
		type: 'horizontalBar',
		data: {
			labels: data.questions.map(q => q.question.question.substring(0, Math.min(q.question.question.length, 30))),
			datasets: datasets,
		},
		options: {
			title: {
				display: true,
				text: 'Procent rätt på quizfrågor',
			},
			responsive: true,
			scales: {
				xAxes: [{
					stacked: true,
				}],
				yAxes: [{
					stacked: true,
				}]
			},
			tooltips: {
				format: "nearest",
				position: "nearest",
				callbacks: {
					title: (tooltipItems: any[], itemData: any) => {
						return data.questions[tooltipItems[0].index].question.question;
					},
					label: (tooltipItem: any, data: any) => {
						const option = datasets[tooltipItem.datasetIndex].options[tooltipItem.index];
						if (option != null) {
							return Math.round(datasets[tooltipItem.datasetIndex].data[tooltipItem.index]*100) + "%: " + option.option.description;
						} else {
							return "";
						}
					}
				}
			},
		}
	};

	const quizstats = <HTMLDivElement>document.createElement("div");

	quizstats.innerHTML = `
	<div class="statistics-member-stats-box">
		<div class="statistics-member-stats-row">
			<span class="statistics-member-stats-type">Median time to answer quiz [s]</span>
			<span class="statistics-member-stats-value">${data.median_seconds_to_answer_quiz}</span>
		</div>
	</div>
	<canvas width=500 height=300></canvas>
	`;
	quizstats.className = "statistics-member-stats";

	const canvas = quizstats.querySelector("canvas")!;
	root.appendChild(quizstats);
	canvas.width = 500;
	canvas.height = 800;
	const ctx = canvas.getContext('2d');
	const chart = new Chart(ctx, config);
}
