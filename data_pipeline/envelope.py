# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import base64
import os

import avro.io
import avro.schema
from cached_property import cached_property
from yelp_avro.avro_string_reader import AvroStringReader
from yelp_avro.avro_string_writer import AvroStringWriter


class Envelope(object):
    """Envelope used to encode and identify a message for transport.

    Envelope instances are meant to be long-lived and used to encode multiple
    messages.

    Example:
        >>> from data_pipeline.message import CreateMessage
        >>> message = CreateMessage(schema_id=1, payload=bytes("FAKE MESSAGE"))
        >>> envelope = Envelope()
        >>> packed_message = envelope.pack(message)
        >>> isinstance(packed_message, bytes)
        True
        >>> unpacked = envelope.unpack(packed_message)
        >>> unpacked['message_type']
        u'create'
        >>> unpacked['schema_id']
        1
        >>> unpacked['payload']
        'FAKE MESSAGE'
    """

    # Magic byte value of packed message specifying that it is base64 encoded
    ASCII_MAGIC_BYTE = bytes('a')

    @cached_property
    def _schema(self):
        # Keeping this as an instance method because of issues with sharing
        # this data across processes.
        schema_path = os.path.join(
            os.path.dirname(__file__),
            'schemas/envelope_v1.avsc'
        )
        return avro.schema.parse(open(schema_path).read())

    @cached_property
    def _avro_string_writer(self):
        return AvroStringWriter(self._schema)

    @cached_property
    def _avro_string_reader(self):
        return AvroStringReader(self._schema, self._schema)

    def pack(self, message, ascii_encoded=False):
        """Packs a message for transport as described in y/cep342.

        Use :func:`unpack` to decode the packed message.

        Args:
            message (data_pipeline.message.Message): The message to pack

        Returns:
            bytes: Avro byte string prepended by magic envelope version byte

        The initial "magic byte" is meant to specify the envelope schema version.
        See y/cep342 for details.  In other words, the version number of the current
        schema is the null byte.  In the event we need to add additional envelope
        versions, we'll use this byte to identify it.

        In addition, the "magic byte" is used as a protocol to encode the serialized
        message in base64. See DATAPIPE-1350 for more detail.
        """
        if ascii_encoded:
            msg = self._avro_string_writer.encode(message.avro_repr)
            return self.ASCII_MAGIC_BYTE + base64.b64encode(msg)
        return bytes(0) + self._avro_string_writer.encode(message.avro_repr)

    def unpack(self, packed_message):
        """Decodes a message packed with :func:`pack`.

        Warning:
            The public API for this function may change to return
            :class:`data_pipeline.message.Message` instances.

        Args:
            packed_message (bytes): The previously packed message

        Returns:
            dict: A dictionary with the decoded Avro representation.
        """

        # If the magic byte is ASCII_MAGIC_BYTE, decode it from base64 to ASCII
        if packed_message[0] == self.ASCII_MAGIC_BYTE:
            return self._avro_string_reader.decode(
                base64.b64decode(packed_message[1:])
            )
        return self._avro_string_reader.decode(packed_message[1:])
