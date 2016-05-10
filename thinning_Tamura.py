#
#
# 細線化（田村の方法）
#

# 細線化サブ（パターンの一致検証、一致ならTrue）
def PatternCheck(int x, int y, int[,] b, int[,,] p):
  bool flg = true;
  int x1, y1;

  for (int h = 0; h < p.GetLength(0); h++)
  {
    flg = true;
    for (int i = -1; i <= 1; i++)
    {
      for (int j = -1; j <= 1; j++)
      {
        x1 = x + j; y1 = y + i;
        if ((x1 >= 0 && x1 < b.GetLength(1)) && (y1 >= 0 && y1 < b.GetLength(0)))
        {
          if (p[h, i + 1, j + 1] >= 0)
          {
            if (p[h, i + 1, j + 1] != b[y1, x1]) flg = false;
          }
        }
        if (!flg) break;
      }
      if (!flg) break;
    }
    if (flg) break;
  }
  return flg;
}

def ProcTamura():
	#除去（D）と例外（K）のパターン設定
	d1 = [
		[[-1, 0, -1], [-1, 1,-1], [-1, -1, -1]],
		[[-1,-1, -1], [-1, 1, 0], [-1, -1, -1]]
		 ]

	k1 = [
			[[-1, 0,-1], [-1, 1, 1], [-1, 1, 0]],
			[[ 0, 1,-1], [ 1, 1, 0], [-1,-1,-1]]
		]

	d2 = [
			[[-1,-1,-1], [-1, 1,-1], [-1, 0,-1]],
			[[-1,-1,-1], [ 0, 1,-1], [-1,-1,-1]]
		]

	k2 = [
			[[ 0, 1,-1], [ 1, 1,-1], [-1, 0,-1]],
			[[-1,-1,-1], [ 0, 1, 1], [-1, 1, 0]]
		]

	kc = [
			[[-1,-1,-1], [ 0, 1, 0}, [-1, 1,-1]],
			[[-1, 0,-1], [ 1, 1,-1], [-1, 0,-1]],
			[[-1, 1,-1], [ 0, 1, 0], [-1,-1,-1]],
			[[-1, 0,-1], [-1, 1, 1], [-1, 0,-1]],
			[[-1,-1,-1], [ 0, 1,-1], [ 1, 0,-1]],
			[[ 1, 0,-1], [ 0, 1,-1], [-1,-1,-1]],
			[[-1, 0, 1], [-1, 1, 0], [-1,-1,-1]],
			[[-1,-1,-1], [-1, 1, 0], [-1, 0, 1]],
			[[ 0, 1, 0], [ 1, 1, 1], [ 0,-1, 0]],
			[[ 0, 1, 0], [-1, 1, 1], [ 0, 1, 0]],
			[[ 0,-1, 0], [ 1, 1, 1], [ 0, 1, 0]],
			[[ 0, 1, 0], [ 1, 1,-1], [ 0, 1, 0]]
		]
  
	#細線化
	lst = []

  do
  {
    #パターン1
	for y in range(bs.Height):
		for x in  range(bs.Width):
			#削除パターン1の検証（一致なら、F1=True）
			f1 = PatternCheck(x, y, b, d1)

			#除外パターン1の検証（一致なら、F2=True）
			if f1 == True:
				f2 = PatternCheck(x, y, b, k1)
				if f2 == True:
					f1 = False
			#除外パターン共通の検証（一致なら、F3=True）
			if f1 == True:
				f3 = PatternCheck(x, y, b, kc)
				if f3 == True:
					f1 = False

        #削除リストに登録（此処で削除しては駄目）
        if f1 == True:
        	lst.append((x, y))

    #パターン2
	if len(lst)> 0:
    	#削除リストに登録された画素を削除
		for i in range(lst.Count):
        	p = lst[i];
        	b[p.Y, p.X] = 0;

		lst.Clear();
		for y in range(bs.Height):
			for x in range(bs.Width):
        		#削除パターン2の検証（一致なら、F1=True）
				f1 = PatternCheck(x, y, b, d2)
				#除外パターン2の検証（一致なら、F2=True）
				if f1 == True:
					f2 = PatternCheck(x, y, b, k2);
					if f2 == True:
						f1 = False;
          		#除外パターン共通の検証（一致なら、F3=True）
				if f1 == True:
					f3 = PatternCheck(x, y, b, kc);
					if f3 == True:
						f1 = False;

				#削除リストに登録（此処で削除しては駄目）
				if f1 == True:
					lst.append((x, y))

		#削除リストに登録された画素を削除
		if len(lst) > 0:
			for i in range(lst.Count):
				p = lst[i]
				b[p.Y, p.X] = 0
  } while (lst.Count > 0);
  