from app.modulespec import MODULES


def test_all_modules_have_interface_and_page(client):
    created=client.post('/api/runs',json={'sample':'night'})
    assert created.status_code == 201
    run=created.json['id']
    for module, (label,_,_) in MODULES.items():
        page=client.get(f'/desk/{module}?run={run}')
        result=client.get(f'/api/modules/{module}/{run}')
        assert page.status_code == 200 and label in page.data.decode()
        assert result.status_code == 200 and result.json['id']==run and result.json['rows']


def test_e2e_differing_samples_and_rerun(client):
    clean=client.post('/api/runs',json={'sample':'clean'}).json
    dirty=client.post('/api/runs',json={'sample':'night'}).json
    assert clean['views']['balance']['tally']['disputed']==0
    assert dirty['views']['balance']['tally']['disputed']==85
    again=client.post(f"/api/runs/{dirty['id']}/rerun").json
    assert again['reused'] and again['manifest']==dirty['manifest']
