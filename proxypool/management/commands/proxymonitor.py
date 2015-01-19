from django.core.management.base import BaseCommand, CommandError
from proxypool.proxypool import ProxyPool

class Command(BaseCommand):
    def handle(self, *args, **options):
        ProxyPool.monitor()
