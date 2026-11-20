MODULES = {
    'calendar': ('冰场日历', '场地', {'line':'源行','key':'冰面','start':'开场','end':'散场','kind':'类别'}),
    'passes': ('包场权益', '队伍', {'line':'源行','key':'权益','owner':'队伍','rink':'冰面','start':'生效','end':'终止','minutes':'分钟额'}),
    'bookings': ('冰面占用', '记录', {'line':'源行','key':'预订','revision':'版','action':'动作','owner':'队伍','rink':'冰面','start':'开始','end':'结束'}),
    'changes': ('换班结转', '结转', {'line':'源行','key':'预订','revision':'版','time':'发生时间','owner':'队伍','rink':'冰面','start':'开始','end':'结束'}),
    'debit': ('有效折抵', '时段', {'day':'营业日','key':'预订','start':'起','end':'讫','status':'处理','debit':'扣券 · 分','cash':'自付 · 分','waived':'豁免 · 分','disputed':'争议 · 分','codes':'原因码'}),
    'balance': ('时券对账', '分钟', {'key':'预订','rink':'冰面','booked':'预订分','debit':'扣券分','cash':'自付分','waived':'豁免分','disputed':'争议分','difference':'差额'}),
    'archive': ('值班归档', '批次', {'key':'批次','created':'生成时间'}),
}
