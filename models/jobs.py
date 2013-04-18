def slow_fib(n):
    if n <= 1:
        return 1
    else:
        return slow_fib(n-1) + slow_fib(n-2)

from gluon.tools import Mail
mail = Mail()
mail.settings.server = 'localhost:2525'
mail.settings.sender = 'you@example.com'
mail.settings.tls = False

