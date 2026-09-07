============================= test session starts ==============================
platform linux -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
rootdir: /mnt/d/Projects/GoldRush2
configfile: pyproject.toml
testpaths: DR2_data_extraction/tests, DR3_data_analytics/tests, DR5_operations/tests
plugins: anyio-4.14.2
collected 842 items / 2 deselected / 840 selected

DR2_data_extraction/tests/test_bis_collector.py ..............           [  1%]
DR2_data_extraction/tests/test_cme_collector.py ....                     [  2%]
DR2_data_extraction/tests/test_cme_futures_collector.py ................ [  4%]
...                                                                      [  4%]
DR2_data_extraction/tests/test_collector_base.py ..........              [  5%]
DR2_data_extraction/tests/test_collector_integration.py ......           [  6%]
DR2_data_extraction/tests/test_collectors_frb_tips.py ..........         [  7%]
DR2_data_extraction/tests/test_fedwatch_collector.py .........           [  8%]
DR2_data_extraction/tests/test_fred_collector.py .........               [  9%]
DR2_data_extraction/tests/test_imf_collector.py ..............           [ 11%]
DR2_data_extraction/tests/test_l0_001.py ...................             [ 13%]
DR2_data_extraction/tests/test_l0_002.py ..................              [ 15%]
DR2_data_extraction/tests/test_l0_003.py ..................              [ 17%]
DR2_data_extraction/tests/test_l0_005.py ..............                  [ 19%]
DR2_data_extraction/tests/test_l0_006.py ..............                  [ 21%]
DR2_data_extraction/tests/test_l0_009.py ..............                  [ 22%]
DR2_data_extraction/tests/test_l10_001.py ................               [ 24%]
DR2_data_extraction/tests/test_l10_002.py ..........                     [ 25%]
DR2_data_extraction/tests/test_l1_001.py ........                        [ 26%]
DR2_data_extraction/tests/test_l1_002.py ........                        [ 27%]
DR2_data_extraction/tests/test_l1_003.py .......                         [ 28%]
DR2_data_extraction/tests/test_l1_004.py .......                         [ 29%]
DR2_data_extraction/tests/test_l1_005.py ........                        [ 30%]
DR2_data_extraction/tests/test_l1_006.py ....                            [ 30%]
DR2_data_extraction/tests/test_l1_006_historical.py .....                [ 31%]
DR2_data_extraction/tests/test_l1_007.py ...........                     [ 32%]
DR2_data_extraction/tests/test_l2_001.py ................                [ 34%]
DR2_data_extraction/tests/test_l2_002.py .................               [ 36%]
DR2_data_extraction/tests/test_l2_003.py .................               [ 38%]
DR2_data_extraction/tests/test_l3_001.py ..............                  [ 40%]
DR2_data_extraction/tests/test_l3_002.py .........                       [ 41%]
DR2_data_extraction/tests/test_l3_003.py ........                        [ 42%]
DR2_data_extraction/tests/test_l3_004.py ................                [ 44%]
DR2_data_extraction/tests/test_l3_005.py ................                [ 46%]
DR2_data_extraction/tests/test_l3_006.py .......................         [ 49%]
DR2_data_extraction/tests/test_l4_001.py ................                [ 50%]
DR2_data_extraction/tests/test_l4_002.py .................               [ 52%]
DR2_data_extraction/tests/test_l4_003.py ................                [ 54%]
DR2_data_extraction/tests/test_l4_004.py ................                [ 56%]
DR2_data_extraction/tests/test_l4_006.py ..............                  [ 58%]
DR2_data_extraction/tests/test_l4_007.py ..............                  [ 60%]
DR2_data_extraction/tests/test_l4_008.py ...........                     [ 61%]
DR2_data_extraction/tests/test_l4_009.py .................               [ 63%]
DR2_data_extraction/tests/test_l5_001.py ..................              [ 65%]
DR2_data_extraction/tests/test_l5_002.py ..................              [ 67%]
DR2_data_extraction/tests/test_l5_003.py .............                   [ 69%]
DR2_data_extraction/tests/test_l5_006.py .................               [ 71%]
DR2_data_extraction/tests/test_l6_001.py ...................             [ 73%]
DR2_data_extraction/tests/test_l6_002.py ...............                 [ 75%]
DR2_data_extraction/tests/test_l7_001.py .................               [ 77%]
DR2_data_extraction/tests/test_l7_003.py ..............                  [ 79%]
DR2_data_extraction/tests/test_l7_004.py .................               [ 81%]
DR2_data_extraction/tests/test_l7_005.py ..................              [ 83%]
DR2_data_extraction/tests/test_l8_001.py .....................           [ 85%]
DR2_data_extraction/tests/test_l9_001.py .....................           [ 88%]
DR2_data_extraction/tests/test_l9_004.py .......................         [ 90%]
DR2_data_extraction/tests/test_ois_directional.py .........              [ 92%]
DR2_data_extraction/tests/test_tranche3_windows.py ..                    [ 92%]
DR2_data_extraction/tests/test_treasury_collector.py ....                [ 92%]
DR2_data_extraction/tests/test_wgc_collector.py .........                [ 93%]
DR2_data_extraction/tests/test_yahoo_collector.py .......                [ 94%]
DR3_data_analytics/tests/test_aggregator.py ........                     [ 95%]
DR3_data_analytics/tests/test_multi_strategy.py ........................ [ 98%]
....                                                                     [ 98%]
DR5_operations/tests/test_cli_extract.py .........                       [100%]

=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/google/genai/types.py:42
  /mnt/d/Projects/GoldRush2/.venv/lib/python3.14/site-packages/google/genai/types.py:42: DeprecationWarning: '_UnionGenericAlias' is deprecated and slated for removal in Python 3.17
    VersionedUnionType = Union[builtin_types.UnionType, _UnionGenericAlias]

DR2_data_extraction/tests/test_l6_001.py: 990 warnings
  /mnt/d/Projects/GoldRush2/DR2_data_extraction/tests/test_l6_001.py:10: DeprecationWarning: The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the future. This includes implicit conversion of bare integers (e.g. `+ 1`).Please use a specific unit instead.
    p=tmp_path/'cache.json'; end=pd.Timestamp(date.today()-timedelta(days=1)); rows=[{'date':(end-pd.Timedelta(days=n-i-1)).date().isoformat(),'value':float(i%10)} for i in range(n)]; p.write_text(json.dumps(rows)); (tmp_path/'L6-001_meta.json').write_text(json.dumps({'source_vintage_date': (date.today()-timedelta(days=1)).isoformat(), 'downloaded_at': date.today().isoformat()})); return p

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=============== 840 passed, 2 deselected, 991 warnings in 51.57s ===============
