from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time


@given('Користувач знаходиться на сторінці авторизації')
def open_login_page(context):
    context.driver = webdriver.Chrome()
    context.driver.get("http://localhost:8000/login/")  # Змінити URL на відповідний
    context.driver.maximize_window()


@when('Користувач вводить логін "{username}" і пароль "{password}"')
def enter_credentials(context, username, password):
    context.driver.find_element(By.ID, "id_username").send_keys(username)
    context.driver.find_element(By.ID, "id_password").send_keys(password)


@when('Натискає кнопку "Увійти"')
def click_login_button(context):
    context.driver.find_element(By.CSS_SELECTOR, ".btn-login").click()
    time.sleep(2)


@then('Користувач бачить текст "{message}" на головній сторінці')
def verify_welcome_message(context, message):
    assert message in context.driver.page_source
    context.driver.quit()


@given('Користувач авторизований і знаходиться на сторінці продукції')
def go_to_products_page(context):
    open_login_page(context)
    enter_credentials(context, "testuser", "password123")
    click_login_button(context)
    context.driver.get("http://localhost:8000/products/")  # URL сторінки продукції


@when('Користувач додає "{product}" до кошика')
def add_to_cart(context, product):
    product_element = context.driver.find_element(By.XPATH, f"//h3[text()='{product}']")
    cart_button = product_element.find_element(By.XPATH, "../..//button")
    cart_button.click()


@when('Переходить до оформлення замовлення')
def go_to_checkout(context):
    context.driver.get("http://localhost:8000/cart/")  # URL кошика
    context.driver.find_element(By.CSS_SELECTOR, ".btn-checkout").click()


@when('Підтверджує замовлення')
def confirm_order(context):
    context.driver.find_element(By.CSS_SELECTOR, ".btn-confirm").click()


@then('Користувач бачить текст "{confirmation_message}"')
def verify_order_confirmation(context, confirmation_message):
    assert confirmation_message in context.driver.page_source
    context.driver.quit()


@given('Користувач авторизований і знаходиться у профілі')
def go_to_profile(context):
    open_login_page(context)
    enter_credentials(context, "testuser", "password123")
    click_login_button(context)
    context.driver.get("http://localhost:8000/profile/")  # URL профілю


@when('Користувач відкриває "Історію замовлень"')
def open_order_history(context):
    context.driver.find_element(By.LINK_TEXT, "Історія замовлень").click()


@then('Користувач бачить список попередніх замовлень із датами та сумами')
def verify_order_history(context):
    orders_table = context.driver.find_element(By.ID, "order-history")
    assert orders_table.is_displayed()
    context.driver.quit()
