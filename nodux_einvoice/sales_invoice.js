// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// print heading
frappe.provide("erpnext.accounts");
erpnext.accounts.SalesInvoiceController = erpnext.selling.SellingController.extend({
	refresh: function(doc, dt, dn) {
		this._super();
		if(cur_frm.msgbox && cur_frm.msgbox.$wrapper.is(":visible")) {
			// hide new msgbox
			cur_frm.msgbox.hide();
		}

		this.frm.toggle_reqd("due_date", !this.frm.doc.is_return);

		this.show_general_ledger();

		if(doc.update_stock) this.show_stock_ledger();

		if(doc.docstatus==1 && !doc.is_return) {

			var is_delivered_by_supplier = false;

			is_delivered_by_supplier = cur_frm.doc.items.some(function(item){
				return item.is_delivered_by_supplier ? true : false;
			})

			if(doc.outstanding_amount >= 0 || Math.abs(flt(doc.outstanding_amount)) < flt(doc.grand_total)) {
				cur_frm.add_custom_button(doc.update_stock ? __('Sales Return') : __('Credit Note'),
					this.make_sales_return, __("Make"));
				cur_frm.page.set_inner_btn_group_as_primary(__("Make"));
			}

			if(cint(doc.update_stock)!=1) {
				// show Make Delivery Note button only if Sales Invoice is not created from Delivery Note
				var from_delivery_note = false;
				from_delivery_note = cur_frm.doc.items
					.some(function(item) {
						return item.delivery_note ? true : false;
					});

				if(!from_delivery_note && !is_delivered_by_supplier) {
					cur_frm.add_custom_button(__('Delivery'), cur_frm.cscript['Make Delivery Note'],
						__("Make"));
				}
			}

			if(doc.outstanding_amount!=0 && !cint(doc.is_return)) {
				cur_frm.add_custom_button(__('Payment'), this.make_payment_entry, __("Make"));
			}

			if(doc.status!=0 && !cint(doc.is_return)) {
				cur_frm.add_custom_button(__('Withholding'), this.make_withholding_out, __("Make"));
			}

			if(doc.outstanding_amount>0 && !cint(doc.is_return)) {
				cur_frm.add_custom_button(__('Payment Request'), this.make_payment_request, __("Make"));
			}
		}
		// Show buttons only when pos view is active
		if (cint(doc.docstatus==0) && cur_frm.page.current_view_name!=="pos" && !doc.is_return) {
			cur_frm.cscript.sales_order_btn();
			cur_frm.cscript.delivery_note_btn();
		}

    if (doc.docstatus == 0) {
			cur_frm.add_custom_button(__("Send SRI"), this.send_sri, __("Make"));
		}

		this.set_default_print_format();
	},

	make_withholding_out: function() {
		frappe.model.open_mapped_doc({
			method: "nodux_withholding_out.withholding_out.invoice_customer.make_withholding_out",
			frm: cur_frm
		})
	},

  send_sri: function(frm) {
		// return frappe.call({
		// 	method: "nodux_einvoice.conexiones.prueba",
		// 	callback: function(r) {
		// 		frm.refresh_fields();
		// 		frm.refresh();
		// 	}
		// })
    frappe.model.open_mapped_doc({
			method: "nodux_einvoice.sale_invoice.action_generate_invoice",
			frm: cur_frm
		})
  }
});

// for backward compatibility: combine new and previous states
$.extend(cur_frm.cscript, new erpnext.accounts.SalesInvoiceController({frm: cur_frm}));
