import python_jsonschema_objects.util as util
import python_jsonschema_objects.validators as validators
import python_jsonschema_objects.pattern_properties as pattern_properties

import copy
import json
import hashlib

import python_jsonschema_objects.wrapper_types

import python_jsonschema_objects  # type: ignore


def hash_dict(d):
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest()


_old_setattr = python_jsonschema_objects.classbuilder.ProtocolBase.__setattr__


def _monkey__setattr__(self, name, val):
    if name.startswith("__donttouch_"):
        object.__setattr__(self, name, val)
        return
    import six
    inverter = dict((v, k) for k, v in six.iteritems(self.__prop_names__))

    # If name is a sanitized version (e.g. base_var) of the actual property (e.g. "base var"), invert it back so that the following lookups work properly.
    # The bigger problem appears to be the fact that the __prop_names__ mapping is somewhat backwards...
    if name in inverter:
        name = inverter[name]
    _old_setattr(self, name, val)

_old_getattr = python_jsonschema_objects.classbuilder.ProtocolBase.__getattr__


def _monkey__getattr__(self, name):
    if name.startswith("__donttouch_"):
        return object.__getattr__(name)
    return _old_getattr(self, name)


python_jsonschema_objects.classbuilder.ProtocolBase.__setattr__ = _monkey__setattr__
python_jsonschema_objects.classbuilder.ProtocolBase.__getattr__ = _monkey__getattr__


# monkey patch HammerProtocolBase
make_property = python_jsonschema_objects.classbuilder.make_property
logger = python_jsonschema_objects.classbuilder.logger
ProtocolBase = python_jsonschema_objects.classbuilder.ProtocolBase


class HammerClassBuilder(python_jsonschema_objects.classbuilder.ClassBuilder):
    # clsdata_hash patch chunk 0
    def _construct(self, uri, clsdata, parent=(ProtocolBase,), **kw):
        if (clsdata.get('type', None) == 'object' or clsdata.get('properties', None) is not None or clsdata.get('additionalProperties', False)):
            if uri in self.resolved:
                if self.resolved[uri].__clsdata_hash__ != hash_dict(clsdata):
                    raise KeyError("uri {0} already exists and is different".format(uri))
        return super()._construct(uri, clsdata, (ProtocolBase,), **kw)

    def _build_object(self, nm, clsdata, parents, **kw):
        logger.debug(util.lazy_format("Building object {0}", nm))

        # clsdata_hash patch chunk 1
        clsdata_hash = hash_dict(clsdata)

        # To support circular references, we tag objects that we're
        # currently building as "under construction"
        self.under_construction.add(nm)

        props = {}
        defaults = set()

        properties = {}
        for p in parents:
            properties = util.propmerge(properties, p.__propinfo__)

        if 'properties' in clsdata:
            properties = util.propmerge(properties, clsdata['properties'])

        name_translation = {}

        for prop, detail in properties.items():
            logger.debug(util.lazy_format("Handling property {0}.{1}",nm, prop))
            properties[prop]['raw_name'] = prop

            # name_translation patch chunk 0
            name_translation[prop] = prop.replace('@', '').replace(' ', '_')
            raw_prop = prop
            prop = name_translation[prop]

            if detail.get('default', None) is not None:
                defaults.add(prop)

            if detail.get('type', None) == 'object':
                # re-use submodules patch chunk 0
                #uri = "{0}/{1}_{2}".format(nm,
                #                           prop, "<anonymous>")
                # Re-use existing submodules if possible
                uri = detail['title']
                # Scrub raw_name since that's a function of this property but not of the substructure.
                detail_clean = dict(detail)
                del detail_clean['raw_name']
                self.resolved[uri] = self.construct(
                    uri,
                    # re-use submodules patch chunk 1
                    detail_clean,
                    (ProtocolBase,))

                props[prop] = make_property(prop,
                                            {'type': self.resolved[uri]},
                                            self.resolved[uri].__doc__)
                # name_translation patch chunk 1
                #properties[prop]['type'] = self.resolved[uri]
                properties[raw_prop]['type'] = self.resolved[uri]


            elif 'type' not in detail and '$ref' in detail:
                ref = detail['$ref']
                uri = util.resolve_ref_uri(self.resolver.resolution_scope, ref)
                logger.debug(util.lazy_format(
                    "Resolving reference {0} for {1}.{2}",
                    ref, nm, prop
                ))
                if uri in self.resolved:
                    typ = self.resolved[uri]
                else:
                    typ = self.construct(uri, detail, (ProtocolBase,))

                props[prop] = make_property(prop,
                                            {'type': typ},
                                            typ.__doc__)
                properties[prop]['$ref'] = uri
                properties[prop]['type'] = typ

            elif 'oneOf' in detail:
                potential = self.resolve_classes(detail['oneOf'])
                logger.debug(util.lazy_format("Designating {0} as oneOf {1}", prop, potential))
                desc = detail[
                    'description'] if 'description' in detail else ""
                props[prop] = make_property(prop,
                                            {'type': potential}, desc
                                            )

            elif 'type' in detail and detail['type'] == 'array':
                if 'items' in detail and isinstance(detail['items'], dict):
                    if '$ref' in detail['items']:
                        uri = util.resolve_ref_uri(
                            self.resolver.resolution_scope,
                            detail['items']['$ref'])
                        typ = self.construct(uri, detail['items'])
                        constraints = copy.copy(detail)
                        constraints['strict'] = kw.get('strict')
                        propdata = {
                            'type': 'array',
                            'validator': python_jsonschema_objects.wrapper_types.ArrayWrapper.create(
                                uri,
                                item_constraint=typ,
                                **constraints)}

                    else:
                        uri = "{0}/{1}_{2}".format(nm,
                                                   prop, "<anonymous_field>")
                        try:
                            if 'oneOf' in detail['items']:
                                typ = TypeProxy([
                                    self.construct(uri + "_%s" % i, item_detail)
                                    if '$ref' not in item_detail else
                                    self.construct(util.resolve_ref_uri(
                                        self.resolver.resolution_scope,
                                        item_detail['$ref']),
                                        item_detail)

                                    for i, item_detail in enumerate(detail['items']['oneOf'])]
                                    )
                            else:
                                # re-use submodules patch chunk 2
                                uri = detail['items']['title']
                                typ = self.construct(uri, detail['items'])

                            constraints = copy.copy(detail)
                            constraints['strict'] = kw.get('strict')
                            propdata = {'type': 'array',
                                        'validator': python_jsonschema_objects.wrapper_types.ArrayWrapper.create(
                                            uri,
                                            item_constraint=typ,
                                            **constraints)}

                        except NotImplementedError:
                            typ = detail['items']
                            constraints = copy.copy(detail)
                            constraints['strict'] = kw.get('strict')
                            propdata = {'type': 'array',
                                        'validator': python_jsonschema_objects.wrapper_types.ArrayWrapper.create(
                                            uri,
                                            item_constraint=typ,
                                            **constraints)}

                    props[prop] = make_property(prop,
                                                propdata,
                                                typ.__doc__)
                elif 'items' in detail:
                    typs = []
                    for i, elem in enumerate(detail['items']):
                        uri = "{0}/{1}/<anonymous_{2}>".format(nm, prop, i)
                        typ = self.construct(uri, elem)
                        typs.append(typ)

                    props[prop] = make_property(prop,
                                                {'type': typs},
                                                )

            else:
                desc = detail[
                    'description'] if 'description' in detail else ""
                uri = "{0}/{1}".format(nm, prop)
                typ = self.construct(uri, detail)

                props[prop] = make_property(prop, {'type': typ}, desc)

        """ If this object itself has a 'oneOf' designation, then
        make the validation 'type' the list of potential objects.
        """
        if 'oneOf' in clsdata:
            klasses = self.resolve_classes(clsdata['oneOf'])
            # Need a validation to check that it meets one of them
            props['__validation__'] = {'type': klasses}

        props['__extensible__'] = pattern_properties.ExtensibleValidator(
            nm,
            clsdata,
            self)

        props['__prop_names__'] = name_translation

        props['__propinfo__'] = properties
        required = set.union(*[p.__required__ for p in parents])

        if 'required' in clsdata:
            for prop in clsdata['required']:
                required.add(prop)

        invalid_requires = [req for req in required if req not in props['__propinfo__']]
        if len(invalid_requires) > 0:
            raise validators.ValidationError("Schema Definition Error: {0} schema requires ""'{1}', but properties are not defined".format(nm, invalid_requires))

        # clsdata_hash patch chunk 2
        props['__clsdata_hash__'] = clsdata_hash
        props['__required__'] = required
        props['__has_default__'] = defaults
        if required and kw.get("strict"):
            props['__strict__'] = True

        props['__title__'] = clsdata.get('title')
        cls = type(str(nm.split('/')[-1]), tuple(parents), props)
        self.under_construction.remove(nm)

        return cls


python_jsonschema_objects.classbuilder.ClassBuilder = HammerClassBuilder
