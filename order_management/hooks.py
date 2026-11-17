app_name = "order_management"
app_title = "Order Management"
app_publisher = "Nguyen Long Vu"
app_description = "Small order management app: orders, status rules and a daily revenue report"
app_email = "nguyenlongvux1@gmail.com"
app_license = "mit"

app_include_js = "/assets/order_management/js/order_management.js"

boot_session = "order_management.boot.boot_session"

before_install = "order_management.setup.install.before_install"
after_install = "order_management.setup.install.after_install"
after_migrate = "order_management.setup.install.after_migrate"
