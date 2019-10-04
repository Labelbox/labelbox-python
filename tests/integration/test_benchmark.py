IMG_URL = "https://picsum.photos/200/300"


def test_benchmark(client, rand_gen):
    project = client.create_project(name=rand_gen(str))
    dataset = client.create_dataset(name=rand_gen(str), projects=project)
    data_row = dataset.create_data_row(row_data=IMG_URL)
    label = project.create_label(data_row=data_row, label="test",
                                 seconds_to_label=0.0)
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

    dataset.delete()
    project.delete()
