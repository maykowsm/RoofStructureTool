import FreeCAD, FreeCADGui, Part, math, os


path_ui = str(os.path.dirname(__file__))+'/EstruturaTelhadoGui.ui'


class EstruturaTelhado_gui():
	def __init__(self):
		self.form = FreeCADGui.PySideUic.loadUi(path_ui)

		#Define a função do botão ok
		self.form.btn_ok.clicked.connect(self.accept)

	def accept(self):
		try:
			#Pega os parametros do formulário Gui
			self.especura = str(self.form.text_especura.text())
			self.largura = str(self.form.text_largura.text())
			self.espacamento = str(self.form.text_espacamento.text())
			self.direcao = str(self.form.text_direcao.text())
		except:
			print('Erro - Verifique os valores de entrada. ')

		try:
			#Pega a lista de subobjetos
			self.subelementos = list(FreeCADGui.Selection.getSelectionEx()[0].SubElementNames)
			self.objeto = FreeCADGui.Selection.getSelection()[0]
		except:
			print('Erro - Selecione as faces do telhado.')


		obj = FreeCAD.ActiveDocument.addObject('Part::FeaturePython','Estrutura Telhado')
		EstruturaTelhado(obj,self.especura, self.largura, self.espacamento, self.direcao, self.subelementos, self.objeto)
		obj.ViewObject.Proxy = 0


		FreeCAD.ActiveDocument.recompute()





class EstruturaTelhado():
	def __init__(self,obj ,especura, largura, espacamento, direcao, subelementos, objeto):
		obj.Proxy = self

		#Criação das propriedades do objeto
		obj.addProperty("App::PropertyLinkSubList","Objetos","Objeto","Face celecionada")

		obj.addProperty("App::PropertyLength","Especura","Dimencoes","Altura dos elementos")
		obj.addProperty("App::PropertyLength","Largura","Dimencoes","Largura dos elementos")
		obj.addProperty("App::PropertyLength","Espacamento","Dimencoes","Espaçamento eixo a eixo dos elementos")
		obj.addProperty("App::PropertyLength","Deslocamento","Dimencoes","Deslocamento dos elementos no plano").Deslocamento = 0

		obj.addProperty("App::PropertyAngle","Direcao","Orientacao","Orientação das peças")

		

		#Passando os parametros para o objeto
		un = FreeCAD.Units.parseQuantity #objeto que converte uma stringa com numeros e letras para unidades do FreeCAD
		obj.Objetos = (objeto, subelementos)
		obj.Especura = un(especura)
		obj.Largura = un(largura)
		obj.Espacamento = un(espacamento)
		obj.Direcao = un(direcao)



	def execute(self,obj):
		'''Função que é executada toda vez que o objeto precisar ser recalulado'''
		
		#------------------------------------------------------------------------
		#Aplica a estrusão nas faces celecionadas
		list_extrusao = []
		for nomeFace in obj.Objetos[0][1]: #Passa na lista de subelementos celecionados
			face = obj.Objetos[0][0].Shape.getElement(nomeFace)
			normal = face.normalAt(0,0)
			print("Normal:", normal)
			list_extrusao.append(face.copy(True).extrude(FreeCAD.Vector(normal[0] * obj.Especura , normal[1] * obj.Especura , normal[2] * obj.Especura )))
		
		if len(list_extrusao) > 1:
			estrusao = Part.Shape.fuse(list_extrusao[0],list_extrusao[1])
			for forma in range(2, len(list_extrusao)):
				nova_estrusao = Part.Shape.fuse(estrusao, list_extrusao[forma])
				estrusao = nova_estrusao
		else:
			estrusao = list_extrusao[0]
		
		# Part.show(estrusao)


		#------------------------------------------------------------------------
		#IIdentifica a maior dimenção do telhado
		selection_box = obj.Objetos[0][0].Shape.BoundBox
		length_max  = 0
		if selection_box.XLength > selection_box.YLength:
			length_max = selection_box.XLength * 1.5
		else:
			length_max = selection_box.YLength * 1.5
		#pega a altura máxima do telhado
		height_max = selection_box.ZLength
		

		#------------------------------------------------------------------------
		#Cria e posiciona o elemento base na origem
		base_retangle = Part.makePlane(length_max, obj.Largura) # Cria o retangulo base
		base_retangle.translate(FreeCAD.Vector(-length_max/2, -obj.Largura/2, 0))#move o elemento base para o centro do sistema de coordenadas
		

		#------------------------------------------------------------------------
		#Cria um grupo de elementos base em linha e rotaciona
		lista_rectangle = [base_retangle]
		
		for i in range(1, int(length_max/obj.Espacamento)):
			#cria uma copia e translada no sentido positivo do eixo y
			lista_rectangle.append(base_retangle.copy(True).translate(FreeCAD.Vector(0, i * obj.Espacamento, 0)))

			#cria uma copia e translada no sentido negativo do eixo y
			lista_rectangle.append(base_retangle.copy(True).translate(FreeCAD.Vector(0, -i * obj.Espacamento, 0)))
		
		group_ratengles =  Part.makeCompound(lista_rectangle)
		# Part.show(group_ratengles)
		cut_retangles = group_ratengles.extrude(FreeCAD.Vector(0,0, 2 * height_max)).translate(FreeCAD.Vector(0,0,-height_max))
		# Part.show(cut_retangles)
		
		#------------------------------------------------------------------------
		#Desloca no plano e rotaciona as peças de corte 
		cut_retangles.translate(FreeCAD.Vector(0, obj.Deslocamento, 0)).rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), obj.Direcao)

		#Posiciona o elemento de no centro do telhado
		cut_retangles.translate(obj.Objetos[0][0].Shape.BoundBox.Center)
		# Part.show(cut_retangles)

		#corta as peças
		part = Part.Shape.common(estrusao, cut_retangles)

		obj.Shape = part








janela = EstruturaTelhado_gui()
FreeCADGui.Control.showDialog(janela)