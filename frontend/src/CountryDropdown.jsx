import React from 'react'

var CountryDropdown = React.createClass({
	getInitialState: function()
	{
		this.continents = [
			{
				name: "Africa",
				countries: [
					{
						name: "Algeria",
						code: "dz"
					},
					{
						name: "Angola",
						code: "ao"
					},
					{
						name: "Benin",
						code: "bj"
					},
					{
						name: "Botswana",
						code: "bw"
					},
					{
						name: "Burkina Faso",
						code: "bf"
					},
					{
						name: "Cameroon",
						code: "cm"
					},
					{
						name: "Cape Verde",
						code: "cv"
					},
					{
						name: "Central African Republic",
						code: "cf"
					},
					{
						name: "Chad",
						code: "td"
					},
					{
						name: "Comoros",
						code: "km"
					},
					{
						name: "Congo",
						code: "cg"
					},
					{
						name: "Congo, The Democratic Republic of the",
						code: "cd"
					},
					{
						name: "Cote d'Ivoire",
						code: "ci"
					},
					{
						name: "Djibouti",
						code: "dj"
					},
					{
						name: "Egypt",
						code: "eg"
					},
					{
						name: "Equatorial Guinea",
						code: "gq"
					},
					{
						name: "Eritrea",
						code: "er"
					},
					{
						name: "Ethiopia",
						code: "et"
					},
					{
						name: "Gabon",
						code: "ga"
					},
					{
						name: "Gambia",
						code: "gm"
					},
					{
						name: "Ghana",
						code: "gh"
					},
					{
						name: "Guinea",
						code: "gn"
					},
					{
						name: "Guinea-Bissau",
						code: "gw"
					},
					{
						name: "Kenya",
						code: "ke"
					},
					{
						name: "Lesotho",
						code: "ls"
					},
					{
						name: "Liberia",
						code: "lr"
					},
					{
						name: "Libya",
						code: "ly"
					},
					{
						name: "Madagascar",
						code: "mg"
					},
					{
						name: "Malawi",
						code: "mw"
					},
					{
						name: "Mali",
						code: "ml"
					},
					{
						name: "Mauritania",
						code: "mr"
					},
					{
						name: "Mauritius",
						code: "mu"
					},
					{
						name: "Mayotte",
						code: "yt"
					},
					{
						name: "Morocco",
						code: "ma"
					},
					{
						name: "Mozambique",
						code: "mz"
					},
					{
						name: "Namibia",
						code: "na"
					},
					{
						name: "Niger",
						code: "ne"
					},
					{
						name: "Nigeria",
						code: "ng"
					},
					{
						name: "Reunion",
						code: "re"
					},
					{
						name: "Rwanda",
						code: "rw"
					},
					{
						name: "Saint Helena",
						code: "sh"
					},
					{
						name: "Sao Tome and Principe",
						code: "st"
					},
					{
						name: "Senegal",
						code: "sn"
					},
					{
						name: "Seychelles",
						code: "sc"
					},
					{
						name: "Sierra Leone",
						code: "sl"
					},
					{
						name: "Somalia",
						code: "so"
					},
					{
						name: "South Africa",
						code: "za"
					},
					{
						name: "South Sudan",
						code: "ss"
					},
					{
						name: "Sudan",
						code: "sd"
					},
					{
						name: "Swaziland",
						code: "sz"
					},
					{
						name: "Tanzania",
						code: "tz"
					},
					{
						name: "Togo",
						code: "tg"
					},
					{
						name: "Tunisia",
						code: "tn"
					},
					{
						name: "Uganda",
						code: "ug"
					},
					{
						name: "Western Sahara",
						code: "eh"
					},
					{
						name: "Zambia",
						code: "zm"
					},
					{
						name: "Zimbabwe",
						code: "zw"
					},
				]
			},
			{
				name: "America",
				countries: [
					{
						name: "Anguilla",
						code: "ai"
					},
					{
						name: "Antigua and Barbuda",
						code: "ag"
					},
					{
						name: "Argentina",
						code: "ar"
					},
					{
						name: "Aruba",
						code: "aw"
					},
					{
						name: "Bahamas",
						code: "bs"
					},
					{
						name: "Barbados",
						code: "bb"
					},
					{
						name: "Belize",
						code: "bz"
					},
					{
						name: "Bermuda",
						code: "bm"
					},
					{
						name: "Bolivia, Plurinational State of",
						code: "bo"
					},
					{
						name: "Brazil",
						code: "br"
					},
					{
						name: "Canada",
						code: "ca"
					},
					{
						name: "Cayman Islands",
						code: "ky"
					},
					{
						name: "Chile",
						code: "cl"
					},
					{
						name: "Colombia",
						code: "co"
					},
					{
						name: "Costa Rica",
						code: "cr"
					},
					{
						name: "Cuba",
						code: "cu"
					},
					{
						name: "Curacao",
						code: "cw"
					},
					{
						name: "Dominica",
						code: "dm"
					},
					{
						name: "Dominican Republic",
						code: "do"
					},
					{
						name: "Ecuador",
						code: "ec"
					},
					{
						name: "El Salvador",
						code: "sv"
					},
					{
						name: "Falkland Islands (Malvinas)",
						code: "fk"
					},
					{
						name: "French Guiana",
						code: "gf"
					},
					{
						name: "Greenland",
						code: "gl"
					},
					{
						name: "Grenada",
						code: "gd"
					},
					{
						name: "Guadeloupe",
						code: "gp"
					},
					{
						name: "Guatemala",
						code: "gt"
					},
					{
						name: "Guyana",
						code: "gy"
					},
					{
						name: "Haiti",
						code: "ht"
					},
					{
						name: "Honduras",
						code: "hn"
					},
					{
						name: "Jamaica",
						code: "jm"
					},
					{
						name: "Martinique",
						code: "mq"
					},
					{
						name: "Mexico",
						code: "mx"
					},
					{
						name: "Montserrat",
						code: "ms"
					},
					{
						name: "Netherlands Antilles",
						code: "an"
					},
					{
						name: "Nicaragua",
						code: "ni"
					},
					{
						name: "Panama",
						code: "pa"
					},
					{
						name: "Paraguay",
						code: "py"
					},
					{
						name: "Peru",
						code: "pe"
					},
					{
						name: "Puerto Rico",
						code: "pr"
					},
					{
						name: "Saint Kitts and Nevis",
						code: "kn"
					},
					{
						name: "Saint Lucia",
						code: "lc"
					},
					{
						name: "Saint Pierre and Miquelon",
						code: "pm"
					},
					{
						name: "Saint Vincent and the Grenadines",
						code: "vc"
					},
					{
						name: "Sint Maarten",
						code: "sx"
					},
					{
						name: "Suriname",
						code: "sr"
					},
					{
						name: "Trinidad and Tobago",
						code: "tt"
					},
					{
						name: "Turks and Caicos Islands",
						code: "tc"
					},
					{
						name: "United States",
						code: "us"
					},
					{
						name: "Uruguay",
						code: "uy"
					},
					{
						name: "Venezuela, Bolivarian Republic of",
						code: "ve"
					},
					{
						name: "Virgin Islands, British",
						code: "vg"
					},
					{
						name: "Virgin Islands, U.S.",
						code: "vi"
					},
				]
			},
			{
				name: "Asia",
				countries: [
					{
						name: "Afghanistan",
						code: "af"
					},
					{
						name: "Armenia",
						code: "am"
					},
					{
						name: "Azerbaijan",
						code: "az"
					},
					{
						name: "Bahrain",
						code: "bh"
					},
					{
						name: "Bangladesh",
						code: "bd"
					},
					{
						name: "Bhutan",
						code: "bt"
					},
					{
						name: "Brunei Darussalam",
						code: "bn"
					},
					{
						name: "Cambodia",
						code: "kh"
					},
					{
						name: "China",
						code: "cn"
					},
					{
						name: "Cyprus",
						code: "cy"
					},
					{
						name: "Georgia",
						code: "ge"
					},
					{
						name: "Hong Kong",
						code: "hk"
					},
					{
						name: "India",
						code: "in"
					},
					{
						name: "Indonesia",
						code: "id"
					},
					{
						name: "Iran, Islamic Republic of",
						code: "ir"
					},
					{
						name: "Iraq",
						code: "iq"
					},
					{
						name: "Israel",
						code: "il"
					},
					{
						name: "Japan",
						code: "jp"
					},
					{
						name: "Jordan",
						code: "jo"
					},
					{
						name: "Kazakhstan",
						code: "kz"
					},
					{
						name: "Korea, Democratic People's Republic of",
						code: "kp"
					},
					{
						name: "Korea, Republic of",
						code: "kr"
					},
					{
						name: "Kuwait",
						code: "kw"
					},
					{
						name: "Kyrgyzstan",
						code: "kg"
					},
					{
						name: "Lao People's Democratic Republic",
						code: "la"
					},
					{
						name: "Lebanon",
						code: "lb"
					},
					{
						name: "Macao",
						code: "mo"
					},
					{
						name: "Malaysia",
						code: "my"
					},
					{
						name: "Maldives",
						code: "mv"
					},
					{
						name: "Mongolia",
						code: "mn"
					},
					{
						name: "Myanmar",
						code: "mm"
					},
					{
						name: "Nepal",
						code: "np"
					},
					{
						name: "Oman",
						code: "om"
					},
					{
						name: "Pakistan",
						code: "pk"
					},
					{
						name: "Palestinian Territory, Occupied",
						code: "ps"
					},
					{
						name: "Philippines",
						code: "ph"
					},
					{
						name: "Qatar",
						code: "qa"
					},
					{
						name: "Saudi Arabia",
						code: "sa"
					},
					{
						name: "Singapore",
						code: "sg"
					},
					{
						name: "Sri Lanka",
						code: "lk"
					},
					{
						name: "Syrian Arab Republic",
						code: "sy"
					},
					{
						name: "Taiwan, Province of China",
						code: "tw"
					},
					{
						name: "Tajikistan",
						code: "tj"
					},
					{
						name: "Thailand",
						code: "th"
					},
					{
						name: "Timor-Leste",
						code: "tl"
					},
					{
						name: "Turkey",
						code: "tr"
					},
					{
						name: "Turkmenistan",
						code: "tm"
					},
					{
						name: "United Arab Emirates",
						code: "ae"
					},
					{
						name: "Uzbekistan",
						code: "uz"
					},
					{
						name: "Viet Nam",
						code: "vn"
					},
					{
						name: "Yemen",
						code: "ye"
					},
				]
			},
			{
				name: "Europe",
				countries: [
					{
						name: "Albania",
						code: "al"
					},
					{
						name: "Andorra",
						code: "ad"
					},
					{
						name: "Austria",
						code: "at"
					},
					{
						name: "Belarus",
						code: "by"
					},
					{
						name: "Belgium",
						code: "be"
					},
					{
						name: "Bosnia and Herzegovina",
						code: "ba"
					},
					{
						name: "Bulgaria",
						code: "bg"
					},
					{
						name: "Croatia",
						code: "hr"
					},
					{
						name: "Czech Republic",
						code: "cz"
					},
					{
						name: "Denmark",
						code: "dk"
					},
					{
						name: "Estonia",
						code: "ee"
					},
					{
						name: "Faroe Islands",
						code: "fo"
					},
					{
						name: "Finland",
						code: "fi"
					},
					{
						name: "France",
						code: "fr"
					},
					{
						name: "Germany",
						code: "de"
					},
					{
						name: "Gibraltar",
						code: "gi"
					},
					{
						name: "Greece",
						code: "gr"
					},
					{
						name: "Holy See (Vatican City State)",
						code: "va"
					},
					{
						name: "Hungary",
						code: "hu"
					},
					{
						name: "Iceland",
						code: "is"
					},
					{
						name: "Ireland",
						code: "ie"
					},
					{
						name: "Italy",
						code: "it"
					},
					{
						name: "Kosovo",
						code: "xk"
					},
					{
						name: "Latvia",
						code: "lv"
					},
					{
						name: "Liechtenstein",
						code: "li"
					},
					{
						name: "Lithuania",
						code: "lt"
					},
					{
						name: "Luxembourg",
						code: "lu"
					},
					{
						name: "Macedonia, The Former Yugoslav Republic of",
						code: "mk"
					},
					{
						name: "Malta",
						code: "mt"
					},
					{
						name: "Moldova, Republic of",
						code: "md"
					},
					{
						name: "Monaco",
						code: "mc"
					},
					{
						name: "Montenegro",
						code: "me"
					},
					{
						name: "Netherlands",
						code: "nl"
					},
					{
						name: "Norway",
						code: "no"
					},
					{
						name: "Poland",
						code: "pl"
					},
					{
						name: "Portugal",
						code: "pt"
					},
					{
						name: "Romania",
						code: "ro"
					},
					{
						name: "Russian Federation",
						code: "ru"
					},
					{
						name: "San Marino",
						code: "sm"
					},
					{
						name: "Serbia",
						code: "rs"
					},
					{
						name: "Slovakia",
						code: "sk"
					},
					{
						name: "Slovenia",
						code: "si"
					},
					{
						name: "Spain",
						code: "es"
					},
					{
						name: "Sweden",
						code: "se"
					},
					{
						name: "Switzerland",
						code: "ch"
					},
					{
						name: "Ukraine",
						code: "ua"
					},
					{
						name: "United Kingdom",
						code: "gb"
					},
				]
			},
			{
				name: "Australia and Oceania",
				countries: [
					{
						name: "American Samoa",
						code: "as"
					},
					{
						name: "Australia",
						code: "au"
					},
					{
						name: "Cook Islands",
						code: "ck"
					},
					{
						name: "Fiji",
						code: "fj"
					},
					{
						name: "French Polynesia",
						code: "pf"
					},
					{
						name: "Guam",
						code: "gu"
					},
					{
						name: "Kiribati",
						code: "ki"
					},
					{
						name: "Marshall Islands",
						code: "mh"
					},
					{
						name: "Micronesia, Federated States of",
						code: "fm"
					},
					{
						name: "Nauru",
						code: "nr"
					},
					{
						name: "New Caledonia",
						code: "nc"
					},
					{
						name: "New Zealand",
						code: "nz"
					},
					{
						name: "Niue",
						code: "nu"
					},
					{
						name: "Norfolk Island",
						code: "nf"
					},
					{
						name: "Northern Mariana Islands",
						code: "mp"
					},
					{
						name: "Palau",
						code: "pw"
					},
					{
						name: "Papua New Guinea",
						code: "pg"
					},
					{
						name: "Pitcairn",
						code: "pn"
					},
					{
						name: "Samoa",
						code: "ws"
					},
					{
						name: "Solomon Islands",
						code: "sb"
					},
					{
						name: "Tokelau",
						code: "tk"
					},
					{
						name: "Tonga",
						code: "to"
					},
					{
						name: "Tuvalu",
						code: "tv"
					},
					{
						name: "Vanuatu",
						code: "vu"
					},
					{
						name: "Wallis and Futuna",
						code: "wf"
					},
				]
			},
			{
				name: "Other areas",
				countries: [
					{
						name: "Bouvet Island",
						code: "bv"
					},
					{
						name: "British Indian Ocean Territory",
						code: "io"
					},
					{
						name: "Canary Islands",
						code: "ic"
					},
					{
						name: "Catalonia",
						code: "catalonia"
					},
					{
						name: "England",
						code: "england"
					},
					{
						name: "European Union",
						code: "eu"
					},
					{
						name: "French Southern Territories",
						code: "tf"
					},
					{
						name: "Guernsey",
						code: "gg"
					},
					{
						name: "Heard Island and McDonald Islands",
						code: "hm"
					},
					{
						name: "Isle of Man",
						code: "im"
					},
					{
						name: "Jersey",
						code: "je"
					},
					{
						name: "Kurdistan",
						code: "kurdistan"
					},
					{
						name: "Scotland",
						code: "scotland"
					},
					{
						name: "Somaliland",
						code: "somaliland"
					},
					{
						name: "South Georgia and the South Sandwich Islands",
						code: "gs"
					},
					{
						name: "Tibet",
						code: "tibet"
					},
					{
						name: "United States Minor Outlying Islands",
						code: "um"
					},
					{
						name: "Wales",
						code: "wales"
					},
					{
						name: "Zanzibar",
						code: "zanzibar"
					},
				]
			},
		];

		return {
			country: this.props.country,
		};
	},

	render: function()
	{
		var _this = this;
		var countries = [];
		var num = 0;
		this.continents.forEach(function(continent, index, array)
		{
			var elm = (
				<li key={num} className="uk-nav-header">{continent.name}</li>
			);
			countries.push(elm);
			num++

			continent.countries.forEach(function(country, index, array)
			{
				var elm = (<li key={country.code}><a onClick={_this.selectCountry} data-country={country.code} className="uk-dropdown-close"><span className={"flag flag-" + country.code}></span> {country.name}</a></li>);
				countries.push(elm);
			});
		});

		return (
			<div data-uk-dropdown="{mode:'click'}" className="uk-button-dropdown">
				<button className="uk-button uk-button-mini"><span className={"flag flag-" + this.state.country}></span> {this.getCountryName(this.state.country)} <i className="uk-icon-angle-down"></i></button>
				<div className="uk-dropdown uk-dropdown-scrollable uk-dropdown-small">
					<ul className="uk-nav uk-nav-dropdown">
						{countries}
					</ul>
				</div>
			</div>
		);
	},

	// Update the country when the props are changed
	componentWillReceiveProps: function(nextProps)
	{
		this.setState({country: nextProps.country.toLowerCase()});
	},

	// Send changes back to parent
	selectCountry: function(event)
	{
		this.props.onChange(event.target.dataset.country);
	},

	// Get a readable name from a country code
	getCountryName: function(code)
	{
		var name = "Unknown";

		this.continents.forEach(function(continent, index, array)
		{
			continent.countries.forEach(function(country, index, array)
			{
				if(country.code == code)
				{
					name = country.name;
					return;
				}
			});

			if(name != "Unknown")
			{
				return;
			}
		});

		return name;
	},
});

module.exports = CountryDropdown