module.exports = {
	childRoutes: [
		{
			path: "economy",
			childRoutes: [
				{
					path: ":period",
					indexRoute: {
						component: require("./Pages/Overview")
					},
					childRoutes: [
						// Overview / Dashboard
						{
							path: "overview",
							component: require("./Pages/Overview")
						},

						// Master ledger
						{
							path: "masterledger",
							component: require("./Pages/MasterLedger")
						},

						// Invoice
						{
							path: "invoice",
							indexRoute: {
								component: require("./Pages/Invoice/List")
							},
							childRoutes: [
								{
									path: "list",
									component: require("./Pages/Invoice/List")
								},
								{
									path: "add",
									component: require("./Pages/Invoice/Add")
								},
								{
									path: ":invoice_id",
									component: require("./Pages/Invoice/Show")
								},
							],
						},

						// Instructions
						{
							path: "instruction",
							component: require("./Pages/Instruction/List")
						},
						{
							path: "instruction/add",
							component: require("./Pages/Instruction/Add")
						},
						{
							path: "instruction/:instruction_number",
							component: require("./Pages/Instruction/Show")
						},
						{
							path: "instruction/:instruction_number/import",
							component: require("./Pages/Instruction/ShowImport")
						},

						// Reports
						{
							path: "valuationsheet",
							component: require("./Pages/ValuationSheet")
						},
						{
							path: "resultreport",
							component: require("./Pages/ResultReport")
						},

						// Cost centers
						{
							path: "costcenter",
							component: require("./Pages/CostCenter/List")
						},
						{
							path: "costcenter/:costcenter_id",
							component: require("./Pages/CostCenter/Show")
						},

						// Accounts
						{
							path: "account/:account_number",
							component: require("./Pages/Account/Show")
						},
					]
				},
			],
		},
		// Settings
		{
			path: "settings",
			childRoutes: [
				{
					path: "economy",
					childRoutes: [
						{
							path: "debug",
							component: require("./Pages/Debug")
						},
						{
							path: "account",
							component: require("./Pages/Account/List")
						},
						{
							path: "account/add",
							component: require("./Pages/Account/Add")
						},
						{
							path: "account/:account_id",
							component: require("./Pages/Account/Show")
						},
						{
							path: "account/:account_id/edit",
							component: require("./Pages/Account/Edit")
						},
						{
							path: "accountingperiod",
							component: require("./Pages/AccountingPeriod/List")
						},
						{
							path: "accountingperiod/add",
							component: require("./Pages/AccountingPeriod/Add")
						},
						{
							path: "accountingperiod/:accountingperiod_id",
							component: require("./Pages/AccountingPeriod/Show")
						},
						{
							path: "accountingperiod/:accountingperiod_id/edit",
							component: require("./Pages/AccountingPeriod/Edit")
						},
					],
				},
			],
		},
	]
}