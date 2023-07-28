ckan.module("editable-config-toggle-field", function ($) {
  /**
   * Disable/enable module host when `control` changes.
   */
  return {
    options: {
      control: null,
    },

    initialize() {
      $.proxyAll(this, /_on/);

      this.control = $(this.options.control).on("change", this._onChange);
    },

    _onChange(event) {
      this.el.prop("disabled", !this.control.prop("checked"));
    },
  };
});
