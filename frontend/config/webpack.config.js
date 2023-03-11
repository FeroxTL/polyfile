const path = require('path');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const BundleTracker = require('webpack-bundle-tracker');


const rootDir = path.resolve(__dirname, '..');
const srcDir = path.resolve(rootDir, 'src');


const bundleTracker = new BundleTracker({
  relativePath: true,
});

const config = {
  context: __dirname,
  entry: {
    dashboard: {
      import: path.resolve(srcDir, 'index.js'),
      dependOn: 'vendor',
    },
    vendor: [path.resolve(srcDir, 'styles/style.scss')],
    blockForm: [path.resolve(srcDir, 'styles/block-form.scss')],
  },
  output: {
    filename: "[name]-[fullhash].js",
    clean: true,
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: 'static/css/[name].[contenthash].css',
      linkType: "text/css",
    }),
    bundleTracker,
  ],
  module: {
    rules: [
      {
        test: /\.(scss|css)$/i,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          "sass-loader",
        ],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'static/img/[hash][ext][query]'
        }
      },
      {
        test: /\.(svg|eot|woff|woff2|ttf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'static/fonts/[hash][ext][query]'
        }
      },
    ],
  },
};


module.exports = (env, argv) => {
  const isDev = argv.mode === 'development';
  let webpackStatsFilename = isDev ? 'webpack-dev-stats.json' : 'webpack-stats.json';
  if (env.hasOwnProperty('stats-filename')) {
    webpackStatsFilename = path.resolve(env["stats-filename"]);
  } else if (argv.hasOwnProperty('outputPath')) {
    webpackStatsFilename = path.resolve(argv.outputPath, '..', webpackStatsFilename);
  }

  bundleTracker.options.filename = webpackStatsFilename;


  if (isDev) {
    config.devtool = 'source-map';
  }

  return config;
};
