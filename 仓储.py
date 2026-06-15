"""
仓储管理系统 - 查询与报表模块
功能：库存查询（精确/模糊/范围）、收发存汇总表、库存预警、库存数量柱状图（可视化）
"""

import importlib.util
import json
import os


def _load_matplotlib():
    """按需加载 matplotlib；若未安装则返回 None。"""
    if importlib.util.find_spec("matplotlib") is None:
        return None, None

    try:
        matplotlib = importlib.import_module("matplotlib")
        plt = importlib.import_module("matplotlib.pyplot")
    except Exception:
        return None, None

    # 设置中文字体，避免图表中文乱码
    matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    return matplotlib, plt

#  文件路径配置 
PRODUCT_FILE = "product_info.txt"
CATEGORY_FILE = "category_info.txt"
SUPPLIER_FILE = "supplier_info.txt"
INBOUND_FILE = "inbound_record.txt"
OUTBOUND_FILE = "outbound_record.txt"

# 数据加载与保存（通用函数） 
def load_data(filename, default_data):
    """加载JSON数据文件，若不存在则创建并返回默认数据"""
    if not os.path.exists(filename):
        save_data(filename, default_data)
        return default_data
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(filename, data):
    """保存数据到JSON文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

#辅助函数 
def get_category_name(category_id, categories):
    """根据categoryId获取categoryName"""
    for cat in categories:
        if cat["id"] == category_id:
            return cat["categoryName"]
    return "未知类别"

def get_supplier_name(supplier_id, suppliers):
    """根据supplierId获取supplierName"""
    for sup in suppliers:
        if sup["id"] == supplier_id:
            return sup["supplierName"]
    return "未知供应商"

def format_product_display(product, categories, suppliers):
    """格式化单个商品的显示（5个字段）"""
    category_name = get_category_name(product["categoryId"], categories)
    supplier_name = get_supplier_name(product["supplierId"], suppliers)
    return f"| {product['id']:6} | {product['productName']:10} | {category_name:8} | {product['quantity']:6} | {supplier_name:12} |"

def print_table_header():
    """打印查询结果表格头"""
    print("-" * 60)
    print("| 编号   | 名称       | 类别     | 数量   | 供应商        |")
    print("-" * 60)

# 1. 精确查询 
def exact_query(products, categories, suppliers):
    """通过商品编号精确查询"""
    print("\n=== 精确查询 ===")
    try:
        pid = int(input("请输入商品编号: "))
    except ValueError:
        print("输入错误：编号必须是数字")
        return
    
    for p in products:
        if p["id"] == pid:
            print_table_header()
            print(format_product_display(p, categories, suppliers))
            print("-" * 60)
            return
    print(f"未找到编号为 {pid} 的商品")

# ================== 2. 模糊查询 ==================
def fuzzy_query(products, categories, suppliers):
    """通过商品名称关键词模糊查询"""
    print("\n=== 模糊查询 ===")
    keyword = input("请输入商品名称关键词: ").strip()
    if not keyword:
        print("关键词不能为空")
        return
    
    results = [p for p in products if keyword in p["productName"]]
    
    if not results:
        print(f"未找到包含 '{keyword}' 的商品")
        return
    
    print_table_header()
    for p in results:
        print(format_product_display(p, categories, suppliers))
    print("-" * 60)
    print(f"共找到 {len(results)} 条记录")

# ================== 3. 库存范围查询 ==================
def range_query(products, categories, suppliers):
    """查询库存数量在指定范围内的商品"""
    print("\n=== 库存范围查询 ===")
    try:
        min_qty = int(input("请输入最小库存数量: "))
        max_qty = int(input("请输入最大库存数量: "))
        if min_qty > max_qty:
            print("最小值不能大于最大值")
            return
    except ValueError:
        print("输入错误：数量必须是数字")
        return
    
    results = [p for p in products if min_qty <= p["quantity"] <= max_qty]
    
    if not results:
        print(f"未找到库存数量在 [{min_qty}, {max_qty}] 之间的商品")
        return
    
    print_table_header()
    for p in results:
        print(format_product_display(p, categories, suppliers))
    print("-" * 60)
    print(f"共找到 {len(results)} 条记录")

# ================== 4. 收发存汇总表（自定义功能1） ==================
def trans_statement_report():
    """
    收发存汇总表
    输出：商品名称 | 期初库存 | 入库总数 | 出库总数 | 期末库存
    注：为简化，期初库存=0，期末=入库-出库+期初
    """
    print("\n=== 收发存汇总表 ===")
    
    products = load_data(PRODUCT_FILE, [])
    categories = load_data(CATEGORY_FILE, [])
    suppliers = load_data(SUPPLIER_FILE, [])
    inbound_records = load_data(INBOUND_FILE, [])
    outbound_records = load_data(OUTBOUND_FILE, [])
    
    # 按商品ID汇总入库和出库数量
    inbound_sum = {}
    outbound_sum = {}
    
    for record in inbound_records:
        pid = record["product_id"]
        inbound_sum[pid] = inbound_sum.get(pid, 0) + record["quantity"]
    
    for record in outbound_records:
        pid = record["product_id"]
        outbound_sum[pid] = outbound_sum.get(pid, 0) + record["quantity"]
    
    # 打印表格
    print("-" * 70)
    print("| 商品名称       | 期初库存 | 入库总数 | 出库总数 | 期末库存 |")
    print("-" * 70)
    
    for p in products:
        pid = p["id"]
        begin = 0  # 简化处理，期初库存=0
        inbound = inbound_sum.get(pid, 0)
        outbound = outbound_sum.get(pid, 0)
        ending = begin + inbound - outbound
        
        print(f"| {p['productName']:12} | {begin:6} | {inbound:6} | {outbound:6} | {ending:6} |")
    
    print("-" * 70)

# ================== 5. 库存预警（自定义功能2） ==================
def stock_warning():
    """
    库存预警：列出库存数量低于安全库存阈值的商品
    注：需要在product_info中增加minStock字段，或手动设定默认阈值
    """
    print("\n=== 库存预警 ===")
    
    products = load_data(PRODUCT_FILE, [])
    categories = load_data(CATEGORY_FILE, [])
    suppliers = load_data(SUPPLIER_FILE, [])
    
    # 方式1：如果product有minStock字段则使用，否则默认阈值=10
    default_min_stock = 10
    warnings = []
    
    for p in products:
        min_stock = p.get("minStock", default_min_stock)
        if p["quantity"] < min_stock:
            warnings.append(p)
    
    if not warnings:
        print(f"所有商品库存充足（低于{default_min_stock}件触发预警）")
        return
    
    print_table_header()
    for p in warnings:
        print(format_product_display(p, categories, suppliers))
        print(f"  ⚠️ 当前库存: {p['quantity']}, 安全库存: {p.get('minStock', default_min_stock)}")
    print("-" * 60)
    print(f"共 {len(warnings)} 种商品库存不足")

# ================== 6. 库存数量柱状图（可视化） ==================
def bar_chart():
    """
    使用 matplotlib 绘制商品库存数量柱状图
    以弹窗形式展示各商品的库存对比
    """
    products = load_data(PRODUCT_FILE, [])

    if not products:
        print("暂无商品数据，无法生成图表")
        return

    _, plt = _load_matplotlib()
    if plt is None:
        print("当前环境未安装 matplotlib，无法生成图表。请安装后再试。")
        return
    
    # 准备数据：商品名称和库存数量
    names = []
    quantities = []
    colors = []
    
    # 颜色列表，用于区分不同商品
    color_palette = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                     '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
    
    for i, p in enumerate(products):
        # 截断过长的商品名称
        name = p['productName'] if len(p['productName']) <= 8 else p['productName'][:7] + '…'
        names.append(name)
        quantities.append(p['quantity'])
        colors.append(color_palette[i % len(color_palette)])
    
    # 创建柱状图
    plt.figure(figsize=(10, 6))
    bars = plt.bar(range(len(names)), quantities, color=colors, edgecolor='white', linewidth=0.5)
    
    # 在柱顶标注数值
    for bar, qty in zip(bars, quantities):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                 str(qty), ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 设置 X 轴标签
    plt.xticks(range(len(names)), names, rotation=30, ha='right', fontsize=9)
    
    # 标题和轴标签
    plt.title('商品库存数量统计图', fontsize=16, fontweight='bold', pad=15)
    plt.xlabel('商品名称', fontsize=12)
    plt.ylabel('库存数量', fontsize=12)
    
    # 添加网格线便于读数
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    print("\n正在生成库存数量柱状图，请查看弹出的图表窗口...")
    plt.show()
    print("图表窗口已关闭")

# ================== 7. 导出查询结果（扩展） ==================
def export_to_file(data, filename, headers):
    """将数据导出到txt文件"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("\t".join(headers) + "\n")
        for row in data:
            f.write("\t".join(str(cell) for cell in row) + "\n")
    print(f"已导出到 {filename}")

# ================== 查询菜单（供主程序调用） ==================
def query_menu():
    """库存查询子菜单"""
    while True:
        print("\n" + "=" * 40)
        print("     库存查询系统")
        print("1. 精确查询（按编号）")
        print("2. 模糊查询（按名称关键词）")
        print("3. 库存范围查询")
        print("4. 收发存汇总表")
        print("5. 库存预警")
        print("6. 库存数量柱状图（可视化）")
        print("0. 返回主菜单")
        print("=" * 40)
        
        choice = input("请选择: ").strip()
        
        # 加载数据
        products = load_data(PRODUCT_FILE, [])
        categories = load_data(CATEGORY_FILE, [])
        suppliers = load_data(SUPPLIER_FILE, [])
        
        if choice == "1":
            exact_query(products, categories, suppliers)
        elif choice == "2":
            fuzzy_query(products, categories, suppliers)
        elif choice == "3":
            range_query(products, categories, suppliers)
        elif choice == "4":
            trans_statement_report()
        elif choice == "5":
            stock_warning()
        elif choice == "6":
            bar_chart()
        elif choice == "0":
            break
        else:
            print("无效选择，请重新输入")
        
        input("\n按回车键继续...")

# ================== 测试入口 ==================
if __name__ == "__main__":
    # 初始化示例数据（仅用于测试，实际运行时会被文件数据覆盖）
    if not os.path.exists(PRODUCT_FILE):
        sample_products = [
            {"id": 1, "productName": "可口可乐", "categoryId": 1, "quantity": 100, "supplierId": 1, "minStock": 20},
            {"id": 2, "productName": "雪碧", "categoryId": 1, "quantity": 5, "supplierId": 1, "minStock": 30},
        ]
        sample_categories = [{"id": 1, "categoryName": "饮料类"}]
        sample_suppliers = [{"id": 1, "supplierName": "成都创新食品生产厂"}]
        save_data(PRODUCT_FILE, sample_products)
        save_data(CATEGORY_FILE, sample_categories)
        save_data(SUPPLIER_FILE, sample_suppliers)
        save_data(INBOUND_FILE, [])
        save_data(OUTBOUND_FILE, [])
    
    # 启动查询菜单
    query_menu()