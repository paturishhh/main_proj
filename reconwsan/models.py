# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone


class Node(models.Model):
    node_id = models.AutoField(primary_key=True)
    node_address_physical = models.CharField(max_length=45)
    node_address_logical = models.CharField(max_length=45)
    node_active = models.IntegerField()
    node_name = models.CharField(max_length=45)

    class Meta:
        # managed = False
        db_table = 'node'
    
    #default when objects.all 
    def __str__(self): 
        return self.node_name


class NodeProbeStatusLog(models.Model):
    probe_status_id = models.AutoField(primary_key=True)
    node = models.ForeignKey('Node', models.CASCADE, null = True)
    probe_time = models.DateTimeField(default = timezone.now)
    node_reply = models.IntegerField()

    class Meta:
        # managed = False
        db_table = 'node_probe_status_log'


class Port(models.Model):
    port_id = models.AutoField(primary_key=True)
    port_number = models.IntegerField()
    node = models.ForeignKey('Node', models.CASCADE, null = True)

    class Meta:
        # managed = False
        db_table = 'port'


class PortConfiguration(models.Model):
    port_configuration_id = models.AutoField(primary_key=True)
    port_configuration_file = models.CharField(max_length=250)
    port_configuration_status = models.CharField(max_length=45, blank=True, null=True)
    data_format = models.CharField(max_length=45)
    port_configuration_version = models.IntegerField()
    user_id = models.IntegerField(blank=True, null=True)
    port_type = models.CharField(max_length=45)
    data_type = models.CharField(max_length=45)
    port = models.ForeignKey('Port', models.CASCADE, null = True)

    class Meta:
        # managed = False
        db_table = 'port_configuration'


class PortValue(models.Model):
    port = models.ForeignKey(Port, models.CASCADE, null = True)
    node = models.ForeignKey(Node, models.CASCADE, null = True)
    port_value = models.CharField(max_length=45)
    time_stamp = models.DateTimeField(default = timezone.now)

    class Meta:
        # managed = False
        db_table = 'port_value'
