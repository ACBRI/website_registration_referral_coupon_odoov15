odoo.define("website_registration_referral_coupon.wrrc", function (require) {
    'use strict';
    var core = require('web.core');
    var _t = core._t;
    var publicWidget = require('web.public.widget');


    publicWidget.registry.registration_referral_coupon = publicWidget.Widget.extend({
        selector: '.o_portal_wrap',
        events: {
            'click #copy_link': 'copylink',
            'click .copy_link': '_copy_text',
            'click .check_availability': 'check_availability',
        },

        _copy_text: function (ev) {
            var self = this;
            ev.preventDefault();
            var $clipboardBtn = this.$(ev.currentTarget);
            $clipboardBtn.popover({
                placement: 'right',
                container: 'body',
                animationType: 'fade',
                offset: '0, 3',
                content: function () {
                    return _t("Copied !");
                }
            });
            var clipboard = new ClipboardJS('.copy_link', {
                text: function () {
                    return $(ev.currentTarget).parent().children('.copy_text').text();
                },
                container: this.el
            });
            clipboard.on('success', function () {
                clipboard.destroy();
                $clipboardBtn.popover('show');
                _.delay(function () {
                    $clipboardBtn.popover('hide');
                }, 800);
            });

            clipboard.on('error', function (e) {
                clipboard.destroy();
            });
        },


        check_availability: function (ev) {
            $.ajax({
                method: "POST",
                url: '/ref_code_availability',
                dataType: 'json',
                data: {
                    'ref_code': $('#reg_ref_code').val(),
                },

                success: function (data) {
                    $('#msg_area').text(data['msg']);
                    $("#msg_area").removeAttr('class');
                    $('#msg_area').addClass(data['classes']);
                    if (data['available'] == true) {
                        $("#submit").removeAttr('disabled');
                        $("#submit").removeClass('pen');
                    }
                    else {
                        $("#submit").attr('disabled', 'disabled');
                        $("#submit").addClass('pen');
                    }
                },
            });
        },

        copylink: function (ev) {
            var self = this;
            ev.preventDefault();
            var $clipboardBtn = this.$('.copy_link');
            $clipboardBtn.popover({
                placement: 'right',
                container: 'body',
                animationType: 'fade',
                offset: '0, 3',
                content: function () {
                    return _t("Copied !");
                }
            });

            var clipboard = new ClipboardJS('.copy_link', {
                text: function () {
                    return $('.copy_link_url').text();
                },
                container: this.el
            });
            clipboard.on('success', function () {
                clipboard.destroy();
                $clipboardBtn.popover('show');
                _.delay(function () {
                    $clipboardBtn.popover('hide');
                }, 800);
            });

            clipboard.on('error', function (e) {
                clipboard.destroy();
            });
        },
    });

    publicWidget.registry.signup_page_load = publicWidget.Widget.extend({
        selector: '.oe_website_login_container',
        events: {
            'focusout #refer_partner': 'checkReferralCodeValidity',
            'click #referral_info': 'showPopOver'
        },

        start: function () {
            var $refer_partner = this.$el.find("#refer_partner")
            var referral_code = $($refer_partner).val()
            if (referral_code) {
                this._checkReferralCodeValidity(referral_code)
            }
            return this._super.apply(this, arguments);
        },

        checkReferralCodeValidity: function (ev) {
            var referral_code = $(ev.currentTarget).val()
            this._checkReferralCodeValidity(referral_code)
        },

        _checkReferralCodeValidity: function (referral_code) {
            var self = this
            $.ajax({
                type: "GET",
                url: "/check/partner/referral_code",
                data: { "referral_code": referral_code },
                success: function (response) {
                    $("#refer_partner").removeClass("is-valid")
                    $("#refer_partner").removeClass("is-invalid")
                    $("#refer_partner").addClass(response)
                    if (response == "is-invalid") {
                        self.$el.find("#refer_partner_error").removeClass("d-none")
                    }
                    else {
                        self.$el.find("#refer_partner_error").addClass("d-none")
                    }
                }
            });
        },
        
        showPopOver: function (ev) {
            var $infoBtn = this.$(ev.currentTarget);
            $infoBtn.popover({
                'trigger': 'focus',
                placement: 'top',
                container: 'body',
                animationType: 'fade',
                offset: '0, 3',
                html: true,
                content: function () {
                    return _t("<strong>Signup using referral code and get reward coupons!</strong>");
                }
            });
        },

    });
});
