var webpack = require('webpack');
const path = require('path');

var src = path.resolve(__dirname, "src")

var mode = process.env.DEVELOPMENT ? 'development' : 'production'
console.info("mode: " + mode);

// Get git info from command line
var commitHash = require("child_process")
	.execSync("sh -c 'find " + src + " -type f -exec md5sum {} \\; | sort -k 2 | md5sum'")
	.toString();

// Get the build date
var options = {
	year: 'numeric', month: 'numeric', day: 'numeric',
	hour: 'numeric', minute: 'numeric', second: 'numeric',
	hour12: false
};
var buildDate = new Intl.DateTimeFormat('sv-SE', options).format(new Date());

module.exports = {
    context: src,
    entry: "./member_app.jsx",

    // Compile into a js.app
    output:
    {
	filename: "member_app.js",
        publicPath: "js",
	path: path.resolve(__dirname, "dist/js"),
    },

    // Preprocess *.jsx files
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: ['babel-loader'],
            },
        ]
    },

    // Files to include.
    resolve: {
        extensions: ['*', '.js', '.jsx']
    },

    // Include build information (build date, git hash)
    plugins: [
        new webpack.DefinePlugin({
            __COMMIT_HASH__: JSON.stringify(commitHash),
            __BUILD_DATE__: JSON.stringify(buildDate),
        })
    ],

    mode: mode,

    // Config for webpack-serve.
    devServer: {
        host: "0.0.0.0",
        port: 8081,
        contentBase: "./dist",
        historyApiFallback: {
            index: "member.html",
        }, 
   }
}
