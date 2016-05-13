# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

from data_pipeline.tools.introspector.base_command import IntrospectorCommand


class SchemaCheckCommand(IntrospectorCommand):
    @classmethod
    def add_parser(cls, subparsers):
        schema_check_command_parser = subparsers.add_parser(
            "schema-check",
            description="Checks the compatibility of an avro schema and all"
                        " given avro_schemas within the given namespace"
                        " and source. Compatibility means that the schema can"
                        " deserialize data serialized by existing schemas within"
                        " all topics and vice-versa.",
            add_help=False
        )

        cls.add_base_arguments(schema_check_command_parser)
        cls.add_source_and_namespace_arguments(schema_check_command_parser)

        schema_check_command_parser.add_argument(
            "schema",
            type=str,
            help="The avro schema to check."
        )

        schema_check_command_parser.set_defaults(
            command=lambda args: cls("data_pipeline_instropsector_schema_check").run(
                args, schema_check_command_parser
            )
        )

    def process_args(self, args, parser):
        super(SchemaCheckCommand, self).process_args(args, parser)
        self.process_source_and_namespace_args(args, parser)
        self.schema = args.schema

    def is_compatible(self):
        is_compatible = self.schematizer.is_avro_schema_compatible(
            avro_schema_str=self.schema,
            source_name=self.source_name,
            namespace_name=self.namespace
        )
        return is_compatible

    def run(self, args, parser):
        self.process_args(args, parser)
        print {"is_compatible": self.is_compatible()}