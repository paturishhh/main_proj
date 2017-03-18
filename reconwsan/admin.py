from django.contrib import admin

# Register your models here.

admin.site.site_header = "ReconWSAN Database Management"
admin.site.site_title = "Database Management"
admin.site.index_title = \
	"Admin"

from .models import Node, NodeProbeStatusLog, Port, PortConfiguration, PortValue

# class NodeAdmin()

admin.site.register(Node)
admin.site.register(NodeProbeStatusLog)
admin.site.register(Port)
admin.site.register(PortConfiguration)
admin.site.register(PortValue)