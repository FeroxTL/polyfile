import m from "mithril";
import {globalNodesData, Node} from "./models/nodes";
import {NodeListWrapperView} from "./views/node_list/index";
import routes from "./utils/routes";
import {parsePath} from "./utils/path";
import LibraryListWrapperView from "./views/library_list/index";
import Auth from "./models/auth";
import {SettingsWrapperView} from "./views/settings";
import {Loader} from "./components/bootstrap/loader";


const NodeListRouter = {
  onmatch: (args, requestedPath) => {
    let path = parsePath(decodeURI(requestedPath)) || "/";
    globalNodesData.fetch(args.lib_id, path);
  },
  render: () => (m(NodeListWrapperView)),
};


const SettingsRouter = {
  onmatch: (args) => {
    const {key = null} = args;

    if (key === null) {
      m.route.set(routes.settings_detail, {key: 'personal'});
    }
  },
  render: (vnode) => (m(SettingsWrapperView, vnode.attrs)),
};


function main() {
  m.render(document.body, m(Loader));

  Auth.getCurrentUser().then(() => {
    m.route(document.body, routes.library_index, {
      [routes.library_index]: LibraryListWrapperView,
      [routes.library_nodes_path]: NodeListRouter,
      [routes.settings]: SettingsRouter,
      [routes.settings_detail]: SettingsRouter,
    });
  }).catch(() => {
    m.render(document.body, m("p", "Error user loading"));
  });
}


main();

//debug
window.m = m;
window.g = globalNodesData;
window.g.Node = Node;