import {getRandomString} from "../../utils/crypto";
import m from "mithril";


//todo: deprecated; use FormInput or FormAutoField
const RawFormInput = {
  view: function (vnode) {
    let {oninput, labelText, value, helpText, id, errorList} = vnode.attrs;
    id = id || getRandomString();
    return (
      m("div.mb-3", [
        labelText && m("label.form-label", {for: id}, labelText),
        m("input.form-control[type=text]", {
          id: id,
          oninput: oninput,
          value: value,
          class: Array.isArray(errorList) && errorList.length > 0 ? "is-invalid" : undefined,
        }),
        errorList && errorList.map((text) => m("div.invalid-feedback.d-block", text)),
        helpText && m("div.form-text", helpText)
      ])
    )
  }
};


const FieldAttrs = function(attrs) {
  this.attribute = attrs["attribute"];
  this.type = attrs["type"] || "text";
  this.required = attrs["required"] || false;
  this.readOnly = attrs["read_only"] || false;
  this.label = attrs["label"] || "";
  this.helpText = attrs["help_text"] || null;
  this.choices = attrs["choices"] || [];
};


const FormInput = {
  oninit: function(vnode) {
    const {fieldAttrs, instance, id=getRandomString()} = vnode.attrs;
    this.id = id;
    this.attribute = fieldAttrs.attribute;
    this.instance = instance;
    if (fieldAttrs.required && this.getValue() === undefined) {
      this.setValue("");
    }
  },

  setValue(value) {
    this.instance[this.attribute] = value;
  },

  getValue: function() {
    return this.instance[this.attribute];
  },

  onInput: function(e) {
    this.setValue(e.target.value);
  },

  view: function (vnode) {
    const {fieldAttrs} = vnode.attrs;
    return (
      m("div.mb-3", [
        fieldAttrs.label && m("label.form-label", {for: this.id}, [
          fieldAttrs.label,
          fieldAttrs.required && m("span.text-danger", " *"),
        ]),
        m("input.form-control[type=text]", {
          id: this.id,
          oninput: this.onInput.bind(this),
          value: this.getValue(),
        }),
        fieldAttrs.helpText && m("div.form-text", fieldAttrs.helpText)
      ])
    )
  }
};


const FormCheckbox = Object.assign(Object.create(FormInput), {
  oninit: function(vnode) {
    FormInput.oninit(vnode);
    const {trueValue=true, falseValue=false} = vnode.attrs;

    this.trueValue = trueValue;
    this.falseValue = falseValue;
  },

  setValue(value) {
    this.instance[this.attribute] = value ? this.trueValue : this.falseValue;
  },

  getValue: function() {
    return this.instance[this.attribute] === this.trueValue;
  },

  onChange: function(e) {
    this.setValue(e.target.checked);
  },

  view: function(vnode) {
    const {fieldAttrs} = vnode.attrs;
    return (
      m("div.mb-3 form-check", [
        m("input.form-check-input[type=checkbox]", {
          id: this.id,
          onchange: this.onChange.bind(this),
          checked: this.getValue(),
        }),
        fieldAttrs.label && m("label.form-label", {for: this.id}, [
          fieldAttrs.label,
          fieldAttrs.required && [" ", m("span.text-danger", "*")],
        ]),
        fieldAttrs.helpText && m("div.form-text", fieldAttrs.helpText)
      ])
    )
  }
});


const FormSelect = Object.assign(Object.create(FormInput), {
  onChange: function(choices, e) {
    this.setValue(choices[e.target.selectedIndex]["value"]);
  },

  view: function(vnode) {
    const {fieldAttrs} = vnode.attrs;

    return (
      m("div.mb-3", [
        fieldAttrs.label && m("label.form-label", {for: this.id}, [
          fieldAttrs.label,
          fieldAttrs.required && [" ", m("span.text-danger", "*")],
        ]),
        m("select.form-select", {
            value: this.getValue(),
            onchange: this.onChange.bind(this, fieldAttrs.choices),
          }, fieldAttrs.choices.map((item) => (m("option", {value: item["value"]}, item["display_name"]))
        )),
        fieldAttrs.helpText && m("div.form-text", fieldAttrs.helpText)
      ])
    )
  }
});

const FormAutoField = {
  view: function(vnode) {
    const {fieldAttrs} = vnode.attrs;

    if (fieldAttrs.readOnly || ["nested object"].indexOf(fieldAttrs.type) !== -1) return null;
    if (fieldAttrs.type === "checkbox") return m(FormCheckbox, vnode.attrs);
    if (["string", "text", "url"].indexOf(fieldAttrs.type) !== -1) return m(FormInput, vnode.attrs);
    if (fieldAttrs.type === "integer") return m(FormInput, vnode.attrs);
    if (fieldAttrs.type === "choice") return m(FormSelect, vnode.attrs);

    console && console.log(`Unknown field type "${fieldAttrs.type}"`);
  }
};


export {RawFormInput, FormInput, FieldAttrs, FormAutoField};
