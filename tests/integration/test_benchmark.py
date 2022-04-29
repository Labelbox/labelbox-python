def test_benchmark(label_pack):
    project, _, data_row, label = label_pack
    assert set(project.benchmarks()) == set()
    assert label.is_benchmark_reference == False

    benchmark = label.create_benchmark()
    assert set(project.benchmarks()) == {benchmark}
    assert benchmark.reference_label() == label
    # Refresh label data to check it's benchmark reference
    label = list(data_row.labels())[0]
    assert label.is_benchmark_reference == True

    benchmark.delete()
    assert set(project.benchmarks()) == set()
    # Refresh label data to check it's benchmark reference
    label = list(data_row.labels())[0]
    assert label.is_benchmark_reference == False
