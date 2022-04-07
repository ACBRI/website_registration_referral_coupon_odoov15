# -*- coding: utf-8 -*-
{
    'name': "Website Refer & Earn Coupons",

    'summary': """Register with referral code and earn reward coupon.""",

    'description': """
        Registration with referral code will gives you discount coupons and additional offers.
        You can easily configure the coupon programs for to the existing customer and the new customer. 
        These rewards coupons will motivate your existing  customers to share there referral code
        and ask the new customers to register and get benefits. This is a way of mutual benefits.  
        So Registration with referral code will give reward coupons to both referring and new customer.
        They  can use these coupons in their future orders and get discounts. 
    """,

    'author': "ErpMstar Solutions",
    'category': 'eCommerce',
    'version': '1.1',

    # any module necessary for this one to work correctly
    'depends': ['website_sale_coupon', 'sale_management'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],

    'images': ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
    'price': 70,
    'currency': 'EUR',
}
