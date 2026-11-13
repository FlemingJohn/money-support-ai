from app.ApplicationFactory import ApplicationFactory
from app.configuration.AppConfiguration import AppConfiguration
from app.ServiceContainer import ServiceContainer

app = ApplicationFactory(ServiceContainer.from_configuration(AppConfiguration())).make()
