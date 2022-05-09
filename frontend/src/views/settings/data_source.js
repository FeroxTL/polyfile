import {Loader} from "../../components/bootstrap/loader";
import m from "mithril";
import {FieldAttrs, FormAutoField, FormInput} from "../../components/bootstrap/form";
import {modal} from "../../components/bootstrap/modal";
import {getCookie} from "../../utils/cookie";


function DataSource(data) {
  this.id = data["id"] || null;
  this.name = data["name"] || "";
  this.dataProviderId = data["data_provider_id"] || null;
  this.options = data["options"] || {};
}


const dataSourceData = {
  list: [],
  status: null,
  optionsData: null,
  optionsStatus: null,

  getUrl: function(instance) {
    if (instance) {
      return m.buildPathname("/api/v1/ds/:id", {id: instance.id})
    }
    return "/api/v1/ds";
  },
  fetch: function() {
    this.list.length = 0;
    this.status = "loading";
    return (
      m.request({
        method: "GET",
        url: this.getUrl(null),
      }).then((result) => {
        this.status = "done";
        this.list = result.map((data) => (new DataSource(data)));
      })
    );
  },
  save: function(instance) {
    return (
      m.request({
        method: instance.id ? "PUT" : "POST",
        url: this.getUrl(instance),
        body: instance,
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
        }
      })
    )
  },
  fetchOptions: function(instance, method) {
    this.optionsStatus = "loading";
    return (
      m.request({
        method: "OPTIONS",
        url: this.getUrl(instance),
      }).then((data) => {
        this.optionsStatus = "done";
        this.optionsData = data["actions"][method].map((data) => (new FieldAttrs(data)));
        return data;
      })
    )
  }
};


function showDataSourceMenu(dataSource) {
  const formData = Object.assign({}, dataSource);
  const dataProviderParams = {
    providerFields: {},
    status: null,
    fetch: function() {
      this.status = "loading";
      return (
        m.request({
          method: "GET",
          url: "/api/v1/dp",
        }).then((result) => {
          this.status = "done";
          for (let provider of result) {
            this.providerFields[provider["id"]] = provider["fields"].map((attrs) => (new FieldAttrs(attrs)));
          }
        }).catch((e) => {
          this.error = e.message;
        })
      );
    }
  };

  dataProviderParams.fetch();
  dataSourceData.fetchOptions(dataSource, "PUT");

  function formSubmit(e) {
    e.preventDefault();
    dataSourceData.save(formData).then((result) => {
      Object.assign(dataSource, result);
      modal.close();
    });
  }

  const EditNodeForm = {
    view: function() {
      if (dataProviderParams.status !== "done" || dataSourceData.optionsStatus !== "done") return m(Loader);

      const optionFields = dataProviderParams.providerFields[formData.dataProviderId];

      return (
        m("form", {onsubmit: formSubmit}, [

          dataSourceData.optionsData.map((fieldAttrs) => (
            m(FormAutoField, {
              instance: formData,
              fieldAttrs: fieldAttrs,
            })
          )),

          m("legend.h5", "Options"),

          optionFields.map((fieldAttrs) => (
            m(FormAutoField, {
              instance: formData.options,
              fieldAttrs: fieldAttrs,
              trueValue: "true",
              falseValue: "false",
            })
          ))
        ])
      )
    }
  };

  const buttonOk = {
    view: () => (m("button.btn btn-primary[type=button]", {onclick: formSubmit}, "Submit"))
  };

  modal.show({
    buttons: [modal.BtnCancel, buttonOk],
    title: "Node settings",
  }, EditNodeForm)
}


const ProviderItemView = {
  view: function(vnode) {
    const {item} = vnode.attrs;

    return [
      m("table.table table-hover mb-0", [
        m("tbody",
          m("tr", [
            m("td", "id"),
            m("td", item.id),
          ]),
          m("tr", [
            m("td", "Data provider"),
            m("td", item.dataProviderId),
          ]),
        ),
      ]),
      m("div.card-footer", [
        m("button.btn btn-secondary[role=button]", {onclick: () => {showDataSourceMenu(item)}}, "Edit")
      ])
    ]
  },
};


const DataProviderAccordion = {
  //todo: add collapsing animation
  oninit: function() {
    this.selectedItem = null;
  },

  selectItem: function(item) {
    if (this.selectedItem === item) {
      this.selectedItem = null;
    } else {
      this.selectedItem = item;
    }
  },

  view: function(vnode) {
    const {items=[]} = vnode.attrs;

    return (
      m("div.accordion", items.map((item) => {
        const isSelected = this.selectedItem === item;

        return (
          m("div.accordion-item", [
            m("h2.accordion-header",
              m("button.accordion-button[type=button]", {
                onclick: this.selectItem.bind(this, item),
                class: isSelected ? null : "collapsed",
              }, m("span", [m("i.fa-solid fa-database me-1"), item.name]))
            ),
            m("div.accordion-collapse collapse border border-primary border-top-0",
              {class: isSelected ? "show" : null},
              m(ProviderItemView, {item: item}),
            )
          ])
        )
      }))
    )
  }
};


const DataSourceSettingsView = {
  verboseName: "Data source",
  iconClass: "fa-solid fa-database",

  oninit: function() {
    return dataSourceData.fetch();
  },

  view: function() {
    if (dataSourceData.status !== 'done') return m(Loader);
    if (dataSourceData.list.length === 0) return m("div.alert.alert-secondary", "No data sources");

    return m(DataProviderAccordion, {items: dataSourceData.list});
  }
};


export default DataSourceSettingsView;
