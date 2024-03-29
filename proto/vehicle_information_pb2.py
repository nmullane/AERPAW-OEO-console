# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: vehicle_information.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x19vehicle_information.proto\x12\x03oeo\"K\n\x12VehicleInformation\x12\n\n\x02id\x18\x01 \x02(\r\x12)\n\x04\x64\x61ta\x18\x02 \x02(\x0b\x32\x1b.oeo.VehicleInformationData\"\xd8\x01\n\x16VehicleInformationData\x12\x1b\n\x06status\x18\x01 \x02(\x0e\x32\x0b.oeo.Status\x12\x17\n\x0f\x62\x61ttery_voltage\x18\x02 \x02(\x02\x12\x17\n\x0f\x62\x61ttery_current\x18\x03 \x02(\x02\x12\x17\n\x0f\x62\x61ttery_percent\x18\x04 \x02(\x02\x12\x10\n\x08latitude\x18\x05 \x02(\x02\x12\x11\n\tlongitude\x18\x06 \x02(\x02\x12\x10\n\x08\x61ltitude\x18\x07 \x02(\x02\x12\x1f\n\x08velocity\x18\x08 \x02(\x0b\x32\r.oeo.Velocity\"+\n\x08Velocity\x12\t\n\x01x\x18\x01 \x02(\x02\x12\t\n\x01y\x18\x02 \x02(\x02\x12\t\n\x01z\x18\x03 \x02(\x02*!\n\x06Status\x12\x0c\n\x08\x44ISARMED\x10\x00\x12\t\n\x05\x41RMED\x10\x01')

_STATUS = DESCRIPTOR.enum_types_by_name['Status']
Status = enum_type_wrapper.EnumTypeWrapper(_STATUS)
DISARMED = 0
ARMED = 1


_VEHICLEINFORMATION = DESCRIPTOR.message_types_by_name['VehicleInformation']
_VEHICLEINFORMATIONDATA = DESCRIPTOR.message_types_by_name['VehicleInformationData']
_VELOCITY = DESCRIPTOR.message_types_by_name['Velocity']
VehicleInformation = _reflection.GeneratedProtocolMessageType('VehicleInformation', (_message.Message,), {
  'DESCRIPTOR' : _VEHICLEINFORMATION,
  '__module__' : 'vehicle_information_pb2'
  # @@protoc_insertion_point(class_scope:oeo.VehicleInformation)
  })
_sym_db.RegisterMessage(VehicleInformation)

VehicleInformationData = _reflection.GeneratedProtocolMessageType('VehicleInformationData', (_message.Message,), {
  'DESCRIPTOR' : _VEHICLEINFORMATIONDATA,
  '__module__' : 'vehicle_information_pb2'
  # @@protoc_insertion_point(class_scope:oeo.VehicleInformationData)
  })
_sym_db.RegisterMessage(VehicleInformationData)

Velocity = _reflection.GeneratedProtocolMessageType('Velocity', (_message.Message,), {
  'DESCRIPTOR' : _VELOCITY,
  '__module__' : 'vehicle_information_pb2'
  # @@protoc_insertion_point(class_scope:oeo.Velocity)
  })
_sym_db.RegisterMessage(Velocity)

if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _STATUS._serialized_start=375
  _STATUS._serialized_end=408
  _VEHICLEINFORMATION._serialized_start=34
  _VEHICLEINFORMATION._serialized_end=109
  _VEHICLEINFORMATIONDATA._serialized_start=112
  _VEHICLEINFORMATIONDATA._serialized_end=328
  _VELOCITY._serialized_start=330
  _VELOCITY._serialized_end=373
# @@protoc_insertion_point(module_scope)
