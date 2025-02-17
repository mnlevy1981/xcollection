import typing

import pydantic
import pytest
import xarray as xr

import xcollection

ds = xr.tutorial.open_dataset('rasm')
dsa = xr.tutorial.open_dataset('air_temperature')


@pytest.mark.parametrize('datasets', [None, {'a': ds, 'b': ds}, {'test': ds.Tair}])
def test_init(datasets):
    c = xcollection.Collection(datasets)
    assert isinstance(c.datasets, dict)
    if datasets is not None:
        assert len(c) == len(datasets)
        assert set(c.keys()) == set(datasets.keys())
    else:
        assert len(c) == 0


def test_repr():
    c = xcollection.Collection({'bar': ds, 'foo': ds})
    assert 'foo' in repr(c)
    assert 'bar' in repr(c)


@pytest.mark.parametrize('datasets', [{'a': ds, 'b': 5}, {1: ds}])
def test_validation_error(datasets):
    with pytest.raises(pydantic.ValidationError):
        xcollection.Collection(datasets)


@pytest.mark.parametrize('value', [1, ds.coords, 'test'])
def test_setitem_validation(value):
    c = xcollection.Collection()
    with pytest.raises(TypeError):
        c['my_key'] = value


def test_setitem():
    c = xcollection.Collection()
    c['my_key'] = ds
    assert len(c) == 1
    assert 'my_key' in c


def test_delitem():
    c = xcollection.Collection({'a': ds, 'b': ds})
    assert len(c) == 2
    assert set(c.keys()) == {'a', 'b'}
    del c['a']
    assert len(c) == 1
    assert set(c.keys()) == {'b'}


def test_getitem():
    datasets = {'a': ds, 'b': ds}
    c = xcollection.Collection(datasets)
    assert isinstance(c['a'], xr.Dataset)
    assert c['a'] is ds
    assert c['b'] is ds

    with pytest.raises(KeyError):
        c['foo']


def test_iter():
    c = xcollection.Collection()
    assert isinstance(iter(c), typing.Iterator)


@pytest.mark.parametrize('data_vars', ['Tair', ['Tair']])
def test_choose_all(data_vars):
    c = xcollection.Collection({'foo': ds, 'bar': ds})
    d = c.choose(data_vars, mode='all')
    assert c == d
    assert set(d.keys()) == {'foo', 'bar'}


def test_choose_all_error():
    c = xcollection.Collection({'foo': ds, 'bar': dsa})
    with pytest.raises(KeyError):
        c.choose('Tair', mode='all')


def test_choose_mode_error():
    c = xcollection.Collection()
    with pytest.raises(ValueError):
        c.choose('Tair', mode='foo')


@pytest.mark.parametrize('data_vars', ['Tair', ['air']])
def test_choose_any(data_vars):
    c = xcollection.Collection({'foo': ds, 'bar': dsa})
    d = c.choose(data_vars, mode='any')
    assert len(d) == 1


@pytest.mark.parametrize('dim, attrs', [('time', {'foo': 'bar'}), (['lat', 'lon'], {})])
def test_map(dim, attrs):
    c = xcollection.Collection({'foo': dsa, 'bar': dsa})

    def func(ds, variable, attrs=None, dim=None):
        result = ds[variable].mean(dim)
        result.attrs = attrs
        return result

    d = c.map(func, args=('air',), attrs=attrs, dim=dim)
    assert set(c.keys()) == set(d.keys())
    xr.testing.assert_identical(d['foo'], func(dsa, 'air', attrs=attrs, dim=dim).to_dataset())


def test_map_type_error():
    c = xcollection.Collection()
    with pytest.raises(TypeError):
        c.map('func')

    with pytest.raises(TypeError):
        c.map(lambda x: x, args=('foo'))
