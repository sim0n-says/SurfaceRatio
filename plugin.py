import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QDialog, QVBoxLayout, QPushButton, QLabel, QComboBox, QListWidget, QLineEdit, QFileDialog
from PyQt5.QtCore import QCoreApplication
from qgis.core import QgsProject
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

class QGISLayerComparator(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SurfaceRatio")
        
        # Créer le layout principal
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Combobox pour sélectionner les couches
        self.layer1_combo = QComboBox()
        self.layout.addWidget(QLabel("Sélectionner la première couche"))
        self.layout.addWidget(self.layer1_combo)
        
        self.layer2_combo = QComboBox()
        self.layout.addWidget(QLabel("Sélectionner la deuxième couche"))
        self.layout.addWidget(self.layer2_combo)
        
        # Labels dynamiques pour afficher le nom des couches sélectionnées
        self.layer1_label = QLabel("Première couche")
        self.layout.addWidget(self.layer1_label)
        
        self.layer2_label = QLabel("Deuxième couche")
        self.layout.addWidget(self.layer2_label)
        
        # Combobox pour sélectionner les champs de la première couche
        self.category_field_combo1 = QComboBox()
        self.layout.addWidget(QLabel("Champ de catégorisation (Première couche)"))
        self.layout.addWidget(self.category_field_combo1)
        
        self.area_field_combo1 = QComboBox()
        self.layout.addWidget(QLabel("Champ de superficie (Première couche)"))
        self.layout.addWidget(self.area_field_combo1)
        
        # Liste pour afficher les catégories uniques de la première couche
        self.category_list1 = QListWidget()
        self.layout.addWidget(QLabel("Catégories (Première couche)"))
        self.layout.addWidget(self.category_list1)
        
        # Combobox pour sélectionner les champs de la deuxième couche
        self.area_field_combo2 = QComboBox()
        self.layout.addWidget(QLabel("Champ de superficie (Deuxième couche)"))
        self.layout.addWidget(self.area_field_combo2)
        
        # Combobox pour choisir entre tableau et graphique
        self.display_choice_combo = QComboBox()
        self.display_choice_combo.addItems(["Graphique", "Tableau"])
        self.layout.addWidget(QLabel("Afficher en tant que"))
        self.layout.addWidget(self.display_choice_combo)
        
        # Combobox pour sélectionner les unités de superficie
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["m²", "km²", "ha"])
        self.layout.addWidget(QLabel("Unité de superficie"))
        self.layout.addWidget(self.unit_combo)
        
        # Champs de texte pour renommer les axes
        self.x_axis_label = QLineEdit()
        self.layout.addWidget(QLabel("Nom de l'axe des X"))
        self.layout.addWidget(self.x_axis_label)
        
        self.y_axis_label = QLineEdit()
        self.layout.addWidget(QLabel("Nom de l'axe des Y"))
        self.layout.addWidget(self.y_axis_label)
        
        # Champ de texte pour renommer le titre du graphique
        self.title_label = QLineEdit()
        self.layout.addWidget(QLabel("Titre du graphique"))
        self.layout.addWidget(self.title_label)
        
        # Bouton pour comparer les couches
        self.compare_button = QPushButton("Comparer les couches")
        self.compare_button.clicked.connect(self.compare_layers)
        self.layout.addWidget(self.compare_button)
        
        # Bouton pour exporter le tableau en CSV
        self.export_table_button = QPushButton("Exporter le tableau en CSV")
        self.export_table_button.clicked.connect(self.export_table_to_csv)
        self.layout.addWidget(self.export_table_button)
        
        # Label pour afficher les résultats
        self.result_label = QLabel()
        self.layout.addWidget(self.result_label)
        
        # Charger les couches disponibles au démarrage
        self.load_layers()
    
    def load_layers(self):
        # Lister les couches disponibles dans le projet QGIS
        layers = QgsProject.instance().mapLayers().values()
        self.layer1_combo.clear()
        self.layer2_combo.clear()
        for layer in layers:
            self.layer1_combo.addItem(layer.name(), layer)
            self.layer2_combo.addItem(layer.name(), layer)
        
        # Charger les champs de la première couche sélectionnée
        self.layer1_combo.currentIndexChanged.connect(self.populate_fields1)
        self.layer2_combo.currentIndexChanged.connect(self.populate_fields2)
        self.layer1_combo.currentIndexChanged.connect(self.update_layer1_label)
        self.layer2_combo.currentIndexChanged.connect(self.update_layer2_label)
        self.populate_fields1()
        self.populate_fields2()
    
    def update_layer1_label(self):
        layer = self.layer1_combo.currentText()
        self.layer1_label.setText(f"Première couche : {layer}")
    
    def update_layer2_label(self):
        layer = self.layer2_combo.currentText()
        self.layer2_label.setText(f"Deuxième couche : {layer}")
    
    def populate_fields1(self):
        # Obtenir la couche sélectionnée
        layer = self.layer1_combo.currentData()
        if not layer:
            return
        
        # Lister les champs de la couche
        fields = [field.name() for field in layer.fields()]
        self.category_field_combo1.clear()
        self.area_field_combo1.clear()
        self.category_field_combo1.addItems(fields)
        self.area_field_combo1.addItems(fields)
        
        # Mettre à jour les catégories uniques lorsque le champ de catégorisation est sélectionné
        self.category_field_combo1.currentIndexChanged.connect(self.update_category_list1)
        self.update_category_list1()
    
    def populate_fields2(self):
        # Obtenir la couche sélectionnée
        layer = self.layer2_combo.currentData()
        if not layer:
            return
        
        # Lister les champs de la couche
        fields = [field.name() for field in layer.fields()]
        self.area_field_combo2.clear()
        self.area_field_combo2.addItems(fields)
    
    def update_category_list1(self):
        # Obtenir la couche et le champ sélectionnés
        layer = self.layer1_combo.currentData()
        category_field = self.category_field_combo1.currentText()
        
        if not layer or not category_field:
            return
        
        # Obtenir les valeurs uniques du champ de catégorisation
        unique_values = layer.uniqueValues(layer.fields().indexFromName(category_field))
        
        # Mettre à jour la liste des catégories
        self.category_list1.clear()
        self.category_list1.addItems(map(str, unique_values))
    
    def categorize_and_sum_area(self, layer, category_field, area_field):
        category_area_sum = defaultdict(float)
        for feature in layer.getFeatures():
            category_value = feature[category_field]
            area_value = feature[area_field]
            category_area_sum[category_value] += area_value
        return category_area_sum
    
    def sum_total_area(self, layer, area_field):
        total_area = 0
        for feature in layer.getFeatures():
            try:
                total_area += float(feature[area_field])
            except ValueError:
                continue  # Skip features with non-numeric area values
        return total_area
    
    def convert_area(self, area, unit):
        if unit == "km²":
            return area / 1e6
        elif unit == "ha":
            return area / 1e4
        return area
    
    def compare_layers(self):
        # Obtenir les couches sélectionnées
        layer1 = self.layer1_combo.currentData()
        layer2 = self.layer2_combo.currentData()
        
        if not layer1 or not layer2:
            self.result_label.setText("Veuillez sélectionner les deux couches")
            return
        
        category_field1 = self.category_field_combo1.currentText()
        area_field1 = self.area_field_combo1.currentText()
        area_field2 = self.area_field_combo2.currentText()
        
        layer1_areas = self.categorize_and_sum_area(layer1, category_field1, area_field1)
        layer2_total_area = self.sum_total_area(layer2, area_field2)
        
        # Convertir les superficies selon l'unité sélectionnée
        unit = self.unit_combo.currentText()
        layer1_areas = {k: self.convert_area(v, unit) for k, v in layer1_areas.items()}
        layer2_total_area = self.convert_area(layer2_total_area, unit)
        
        comparison = self.compare_areas(layer1_areas, layer2_total_area)
        
        display_choice = self.display_choice_combo.currentText()
        if display_choice == "Graphique":
            self.generate_plot(comparison, layer1_areas, layer2_total_area, unit)
        else:
            self.generate_table(comparison, layer1_areas, layer2_total_area, unit)
    
    def compare_areas(self, layer1_areas, layer2_total_area):
        comparison = {}
        for category, area in layer1_areas.items():
            proportion = area / layer2_total_area
            comparison[category] = proportion
        return comparison
    
    def generate_plot(self, comparison, layer1_areas, layer2_total_area, unit):
        categories = list(comparison.keys())
        proportions = list(comparison.values())
        areas = [layer1_areas[cat] for cat in categories]
        
        # Ajouter une barre pour la somme de toutes les catégories
        total_area_layer1 = sum(areas)
        categories.append(f'Total {self.layer1_combo.currentText()}')
        proportions.append(total_area_layer1 / layer2_total_area)
        areas.append(total_area_layer1)
        
        fig, ax = plt.subplots(figsize=(12, 6))  # Augmenter la taille de la figure
        bars = ax.bar(categories, proportions, color=plt.cm.tab20.colors[:len(categories)])  # Utiliser des couleurs personnalisées
        ax.set_xlabel(self.x_axis_label.text() or self.category_field_combo1.currentText())  # Default to category field name
        ax.set_ylabel(self.y_axis_label.text() or 'Répartition en %')  # Default to 'Répartition en %'
        ax.set_title(self.title_label.text() or f'Comparaison des superficies par catégorie ({self.layer1_combo.currentText()}) vs Superficie totale ({self.layer2_combo.currentText()})')
        ax.set_xticks(np.arange(len(categories)))
        ax.set_xticklabels(categories, rotation=45, ha='right')  # Faire pivoter les étiquettes des catégories
        ax.set_ylim(0, max(proportions) * 1.2)  # Ajuster les limites de l'axe y pour plus d'espace
        
        # Ajouter des annotations pour afficher les valeurs des proportions et les superficies sur les barres
        for bar, area in zip(bars, areas):
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval, f'{round(yval*100, 2)}%\n({round(area, 2)})', va='bottom', ha='center')  # va='bottom' pour placer le texte au-dessus des barres
        
        plt.tight_layout()  # Ajuster automatiquement les sous-éléments pour qu'ils s'adaptent à la figure
        plt.show()
    
    def generate_table(self, comparison, layer1_areas, layer2_total_area, unit):
        categories = list(comparison.keys())
        proportions = list(comparison.values())
        areas = [layer1_areas[cat] for cat in categories]
        
        # Ajouter une ligne pour la somme de toutes les catégories
        total_area_layer1 = sum(areas)
        categories.append(f'Total {self.layer1_combo.currentText()}')
        proportions.append(total_area_layer1 / layer2_total_area)
        areas.append(total_area_layer1)
        
        # Créer une fenêtre de dialogue pour afficher le tableau
        table_dialog = QDialog(self)
        table_dialog.setWindowTitle("SurfaceRatio - Tableau")
        table_layout = QVBoxLayout()
        table_dialog.setLayout(table_layout)
        
        # Créer le tableau
        table = QListWidget()
        table_layout.addWidget(table)
        
        # Ajouter les en-têtes
        table.addItem("Catégorie\tSuperficie\tProportion")
        
        # Ajouter les données
        for category, area, proportion in zip(categories, areas, proportions):
            table.addItem(f"{category}\t{round(area, 2)}\t{round(proportion*100, 2)}%")
        
        # Ajouter la somme des superficies de la couche 2
        table.addItem(f"Total {self.layer2_combo.currentText()}\t{round(layer2_total_area, 2)}\t100%")
        
        # Afficher la fenêtre de dialogue
        table_dialog.exec_()
    
    def export_table_to_csv(self):
        # Obtenir les couches sélectionnées
        layer1 = self.layer1_combo.currentData()
        layer2 = self.layer2_combo.currentData()
        
        if not layer1 or not layer2:
            self.result_label.setText("Veuillez sélectionner les deux couches")
            return
        
        category_field1 = self.category_field_combo1.currentText()
        area_field1 = self.area_field_combo1.currentText()
        area_field2 = self.area_field_combo2.currentText()
        
        layer1_areas = self.categorize_and_sum_area(layer1, category_field1, area_field1)
        layer2_total_area = self.sum_total_area(layer2, area_field2)
        
        # Convertir les superficies selon l'unité sélectionnée
        unit = self.unit_combo.currentText()
        layer1_areas = {k: self.convert_area(v, unit) for k, v in layer1_areas.items()}
        layer2_total_area = self.convert_area(layer2_total_area, unit)
        
        comparison = self.compare_areas(layer1_areas, layer2_total_area)
        
        # Préparer les données pour le CSV
        categories = list(comparison.keys())
        proportions = list(comparison.values())
        areas = [layer1_areas[cat] for cat in categories]
        
        # Ajouter une ligne pour la somme de toutes les catégories
        total_area_layer1 = sum(areas)
        categories.append(f'Total {self.layer1_combo.currentText()}')
        proportions.append(total_area_layer1 / layer2_total_area)
        areas.append(total_area_layer1)
        
        # Créer un DataFrame pandas
        df = pd.DataFrame({
            'Catégorie': categories,
            'Superficie': areas,
            'Proportion': [p * 100 for p in proportions]
        })
        
        # Ajouter la somme des superficies de la couche 2
        total_row = pd.DataFrame({
            'Catégorie': [f'Total {self.layer2_combo.currentText()}'],
            'Superficie': [layer2_total_area],
            'Proportion': [100]
        })
        df = pd.concat([df, total_row], ignore_index=True)
        
        # Demander à l'utilisateur de choisir un fichier pour enregistrer le CSV
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Enregistrer le fichier", "", "CSV Files (*.csv);;All Files (*)", options=options)
        
        if file_path:
            # Enregistrer le DataFrame dans un fichier CSV
            df.to_csv(file_path, index=False)
            self.result_label.setText(f"Tableau exporté vers {file_path}")

class SurfaceRatioPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = self.tr(u'&SurfaceRatio')
        self.toolbar = self.iface.addToolBar(u'SurfaceRatio')
        self.toolbar.setObjectName(u'SurfaceRatio')

    def tr(self, message):
        return QCoreApplication.translate('SurfaceRatio', message)

    # Initialisation de l'interface utilisateur du plugin
    def initGui(self):
        # Chemin de l'icône du plugin
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
        # Création de l'action du plugin avec l'icône et le nom
        self.action = QAction(QIcon(icon_path), "SurfaceRatio", self.iface.mainWindow())
        # Connexion de l'action à la méthode run
        self.action.triggered.connect(self.run)
        # Ajout de l'icône du plugin à la barre d'outils de QGIS
        self.iface.addToolBarIcon(self.action)
        # Ajout du plugin au menu de QGIS
        self.iface.addPluginToMenu("&SurfaceRatio", self.action)

    # Déchargement du plugin
    def unload(self):
        # Suppression de l'icône du plugin de la barre d'outils de QGIS
        self.iface.removeToolBarIcon(self.action)
        # Suppression du plugin du menu de QGIS
        self.iface.removePluginMenu("&SurfaceRatio", self.action)

    def add_action(self, icon_path, text, callback, parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        self.iface.addPluginToMenu(self.menu, action)
        self.toolbar.addAction(action)
        self.actions.append(action)
        return action

    def run(self):
        dialog = QGISLayerComparator()
        dialog.exec_()