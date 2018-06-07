var webpack = require('webpack');

// Get git info from command line
var commitHash = require("child_process")
	.execSync("git rev-parse --short HEAD")
	.toString();

// Get the build date
var options = {
	year: 'numeric', month: 'numeric', day: 'numeric',
	hour: 'numeric', minute: 'numeric', second: 'numeric',
	hour12: false
};
var buildDate = new Intl.DateTimeFormat('sv-SE', options).format(new Date());

module.exports = {
	context: __dirname + "/src",
	entry: "./app.jsx",

	// Compile into a js.app
	output:
	{
		filename: "app.js",
		path: __dirname + "/dist/js",
	},

	// Include *.js and *.jsx files
	resolve: {
		extensions: ["", ".js", ".jsx"]
	},

	// Preprocess *.jsx files
	module: {
		loaders:
		[
			{
				test: /\.jsx?$/,
				exclude: /node_modules/,
				loader: "babel-loader",
				query: {
					presets: ["es2015", "react"]
				}
			},
		],
	},

	// Include build information (build date, git hash)
	plugins: [
		new webpack.DefinePlugin({
			__COMMIT_HASH__: JSON.stringify(commitHash),
			__BUILD_DATE__: JSON.stringify(buildDate),
		})
	]
}