from flask import Flask, render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

playstore = pd.read_csv('data/googleplaystore.csv')

#playstore._________(subset = ___________________) 
playstore = playstore.drop_duplicates(keep='first')

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore = playstore.drop([10472])

playstore['Category'] = playstore['Category'].astype('category')

# Buang tanda koma(,) dan tambah(+) kemudian ubah tipe data menjadi integer
#playstore['Installs'] = ________.apply(lambda x: x.replace(______))
#playstore['Installs'] = ________.apply(lambda x: x.replace(______))
#playstore['Installs'] = ___________________________
playstore['Installs'] = playstore['Installs'].str.replace('+', '').str.replace(',', '')

# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

#________ = _______.apply(lambda x: x.replace(______))
#________ = __________________________________
playstore['Price'] = playstore['Price'].str.replace('$', '')
playstore['Price'] = playstore['Price'].astype('float64')

# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
playstore[['Reviews', 'Size', 'Installs']] = playstore[['Reviews', 'Size', 'Installs']].astype('int64')

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

    # Statistik
    top_category = pd.crosstab(
        index=df2['Category']
        ,columns="Jumlah"
    ).sort_values('Jumlah', ascending=False)
    top_category = top_category.reset_index()

    df3 = df2.groupby(['Category','App','Rating'])['Reviews'].max()
    rev_table = df3.sort_values(ascending=False).head(10).reset_index()
    
    # Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        'most_categories' : top_category['Category'].iloc[0],
        'total': top_category['Jumlah'].iloc[0],
        'rev_table' : rev_table.to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    #### Bar Plot
    cat_order = df2.groupby('Category').agg({
        'Reviews' : 'count'
    }).rename({'Category':'Total'}, axis=1).sort_values(by='Reviews', ascending=False).head()
    cat_order = cat_order.reset_index()

    X = df2['Reviews'].values
    Y = df2['Category'].values

    my_colors = ['r','g','b','k','y','m','c']
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()

    # bagian ini digunakan untuk membuat bar plot
    plt.barh(cat_order['Category'], cat_order['Reviews'], color=my_colors)

    # bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('cat_order.png',bbox_inches="tight") 

    # bagian ini digunakan untuk mengconvert matplotlib png ke base64 agar dapat ditampilkan ke template html
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
    # halaman html
    result = str(figdata_png)[2:-1]
    
    #### Scatter Plot
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = df2['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot

    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()

    # isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=X,y=Y, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    #### Histogram Size Distribution
    X=(df2['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(x=X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]

    #### Buatlah sebuah plot yang menampilkan insight di dalam data 
    ## insight 1 : category FAMILY mengalami kenaikan reviews yang signifikan dari tahun 2017 ke 2018
    ## insight 2 : category FAMILY mengalami penurunan reviews dari tahun 2014 ke 2015    
    plot_line = df2[df2['Category'] == top_category['Category'].iloc[0]]
    plot_line['Last Updated'] = pd.to_datetime(plot_line['Last Updated'])
    #plot_line.info()
    plot_line['Year'] = plot_line['Last Updated'].dt.to_period('Y')
    plot_line.head(3)

    df_plot_line = plot_line.pivot_table(
        index='Year',
        columns='Category',
        values='Reviews',
        aggfunc='mean',
        observed=True
    )
    df_plot_line = df_plot_line.reset_index()
    df_plot_line['Year'] = df_plot_line['Year'].astype('string')
    #df_plot_line
    #df_plot_line.info()

    fig = plt.figure(figsize=(10,5))
    fig.add_subplot()

    plt.plot(df_plot_line['Year'], df_plot_line['FAMILY'], label='FAMILY')
    plt.xlabel('Tahun')
    plt.ylabel('Rata - rata Reviews')
    plt.legend(title='Category')
    plt.savefig('plot_line.png')

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result4 = str(figdata_png)[2:-1]

    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3, result4=result4)

if __name__ == "__main__": 
    app.run(debug=True)    
