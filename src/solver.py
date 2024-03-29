from prob_builder import *
from datetime import datetime

def assign_order_to_car(order, car_list):
    filtered_cars = list(filter(lambda car: car.start_center == order.terminal_ID and car.doable(order), car_list))
    if not filtered_cars:
        available_cars = list(filter(lambda car: car.doable(order), car_list))
        filtered_cars = available_cars

    closest_car = None
    if filtered_cars:
        closest_car = min(filtered_cars, key=lambda car: distance.calculate_distance_time(car.start_center, order.arrive_id)[0])

    return closest_car

def perform_loading(order, car, date, group_list):
    car.loading(order)
    target_time = datetime.strptime(date + group_list[order.group], "%Y-%m-%d%H:%M")
    car.now_time = max(car.now_time, target_time)
    car.completed_orders.append(order)

def rule_solver(prob_instance):
    print('solver start')

    ord_list = prob_instance.ord_list
    for ord in ord_list:
        ord.initialize()

    car_list = prob_instance.car_list
    for car in car_list:
        car.initialize()
        car.completed_orders = []

    group_time_windows = {
        0: [datetime.strptime("00:00", "%H:%M").time(), datetime.strptime("18:00", "%H:%M").time()],
        1: [datetime.strptime("07:00", "%H:%M").time(), datetime.strptime("10:00", "%H:%M").time()],
        2: [datetime.strptime("07:00", "%H:%M").time(), datetime.strptime("10:00", "%H:%M").time(),
            datetime.strptime("13:00", "%H:%M").time()],
        3: [datetime.strptime("18:00", "%H:%M").time()]
    }

    date_list = [
        '2023-05-01',
        '2023-05-02',
        '2023-05-03',
        '2023-05-04',
        '2023-05-05',
        '2023-05-06',
        '2023-05-07'
    ]

    group_list = [
        '00:00',
        '06:00',
        '12:00',
        '18:00'
    ]

    orderResult_table = OrderResult(None, None, None, None, None, None, None, None, None) # 맨 첫 항 다 None이라 지워야함
    load = 0
    unload = 0
    total_load = 0
    total_unload = 0
    sequence = 0 # 할당된 배송 시퀀스
    pending_orders = []

    for date in date_list:
        for group in range(4):
            pending_orders.sort(key=lambda order: order.date)
            group_orders = pending_orders
            pending_orders = []
            undelivered_orders = [order for order in ord_list if not order.delivered]

            for order in undelivered_orders:
                if order.group == group and order.date == date:
                    if order.time_window[0].time() in group_time_windows[group]:
                        group_orders.append(order)
                    else:
                        pending_orders.append(order)

            for order in group_orders:
                closest_car = assign_order_to_car(order, car_list)
                if closest_car:
                    perform_loading(order, closest_car, date, group_list)
                    load += 1
                else:
                    pending_orders.append(order)

            for car in [car for car in car_list if not car.can_move]:
                car.served_order.sort(
                    key=lambda order: distance.calculate_distance_time(car.start_center, order.arrive_id)[0])

            for car in car_list:
                if car.can_move == False:
                    for order in car.served_order:
                        if order in group_orders:
                            car.unloading(order)
                            orderResult_table.add_row(Order_No=order.ord_no, VehicleID=car.vehicle_id, Sequence=0,
                                                      SiteCode=car.start_center, Delivered=0)
                            print(orderResult_table.get_order_table())  # -> 예시입니당 이 테이블에 값 넣을 때 (add_row) 주문 배치될 때 넣어야하니까 위치 파악하고 코드 넣어야함!
                            unload += 1
                    car.served_order = []

            while True:
                delay = 0
                for order in pending_orders:
                    closest_car = assign_order_to_car(order, car_list)
                    if closest_car:
                        perform_loading(order, closest_car, date, group_list)
                        load += 1
                        delay += 1

                for car in filter(lambda car: not car.can_move, car_list):
                    car.served_order.sort(
                        key=lambda order: distance.calculate_distance_time(car.start_center, order.arrive_id)[0])

                for car in car_list:
                    if car.can_move == False:
                        for order in car.served_order:
                            if order in pending_orders:
                                car.unloading(order)
                                unload += 1
                        car.served_order = []

                if delay == 0:
                    break

        print(date, '총 상차 주문 수:', load)
        print(date, '총 하차 주문 수:', unload)
        total_load += load
        total_unload += unload
        load = 0
        unload = 0

    print('상차 작업 완료 수', total_load)
    print('하차 작업 완료 수', total_unload)


    objective = 0
    vehicleId = car_list[-1]

    for car in car_list:    # 운영비용 계산
        objective += car.total_fixed_cost + car.travel_distance * car.variable_cost

    total_distance = sum(map(lambda car: car.travel_distance, car_list))
    total_fixedCost = sum(map(lambda car: car.total_fixed_cost, car_list))
    total_variableCost = sum(map(lambda car: car.variable_cost, car_list))
    total_volume = sum(map(lambda car: car.max_capa, car_list))

    solution = {}
    solution['Objective'] = objective # TotalCost
    result_table = CarResult(vehicleId, total_unload, total_volume, total_distance, 0, 0, 0, 0, objective, total_fixedCost, total_variableCost)
    return result_table.car_table()