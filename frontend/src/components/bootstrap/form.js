import {getRandomString} from "../../utils/crypto";
import m from "mithril";


let FormInput = {
  view: function (vnode) {
    let {oninput, labelText, value, helpText, id} = vnode.attrs;
    id = id || getRandomString();
    return (
      m("div.mb-3", [
        labelText && m("label.form-label", {for: id}, labelText),
        m("input.form-control[type=text]", {
          id: id,
          oninput: oninput,
          value: value,
        }),
        helpText && m("div.form-text", helpText)
      ])
    )
  }
};


export {FormInput};
